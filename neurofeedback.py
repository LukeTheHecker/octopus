import neuroFeedbackViz as nfv
import workers
import numpy as np
import time

class BaseNeuroFeedback:
    ''' Process data and plot it on a canvas.'''
    def __init__(self, ProcessFunction, canvas, threadpool, gatherer, 
        *args, timeRangeProcessed=0.25, channelsOfInterest=None, 
        scoreMemorySize=10, **kwargs):
        ''' 
        Parameters:
        -----------
        ProcessFunction : function, function with which the data will be processed.
        timeRangeProcessed : float, time in seconds 
        blocksPerSecond : int, number of blocks per second (given by Brain Vision RDA)
        indicesOfInterest : list, indices of electrodes on which the metric should be calculated
        args/kwargs : lists/dict, variable arguments for the ProcessFunction
        '''

        self.BlocksProcessed = 1
        self.BlocksVisualized = 0
        self.ProcessFunction = ProcessFunction
        self.canvas = canvas
        self.threadpool = threadpool
        self.gatherer = gatherer
        self.timeRangeProcessed = timeRangeProcessed
        self.blocksPerSecond = gatherer.blocks_per_s
        self.channelsOfInterest = channelsOfInterest 
        self.indicesOfInterest = [gatherer.channelNames.index(chan) for chan in channelsOfInterest]
        self.blockDurS = 1 / float(self.blocksPerSecond)
        self.minNumberOfBlocks = int(round(self.blocksPerSecond * self.timeRangeProcessed))
        self.cal = None
        self.scoreMemory = [np.nan] * scoreMemorySize
        self.args = args
        self.kwargs = kwargs

        self.NF_worker = workers.SignallingWorker(self.update)
        self.NF_worker.signals.result.connect(nfv.BarPlotAnimation)  # nfv.circleAnimation
        self.threadpool.start(self.NF_worker)
    
    def calibrate(self, dataMemory, blockMemory):
        if all(blockMemory[:10] == -1 ):
            return
        print("enough data to calibrate!")
        dataMemoryDurS = len(blockMemory) * self.blockDurS
        numberOfChunks = dataMemoryDurS / self.timeRangeProcessed
        # Get dataMemory in consistent shape
        dataMemory = self.handleDataInput(dataMemory)
        # Calculate properties of the data (e.g. sampling rate)
        self.calculate_data_properties(dataMemory, blockMemory)
        # Create chunks of the whole data Memory to process individually
        # Ensure the dataMemory is evenly divisible by numberOfChunks:
        while dataMemory.shape[1] % numberOfChunks != 0:
            numberOfChunks -= 1
        dataChunks = np.split(dataMemory[self.indicesOfInterest, :], numberOfChunks, axis=1)
        # Process the chunks
        scoreList = list()
        for chunk in dataChunks:
            chunk = np.array(chunk)
            tmp_score = list()
            for elec in range(chunk.shape[0]):
                score = self.ProcessFunction(np.squeeze(chunk[elec, :]), *self.args, **self.kwargs)
                tmp_score.append( score )
                # print(f'chunk[elec, :] {chunk[elec, :]} of type {type(chunk[elec, :])} yielded {score}')
                # print(f'self.args={self.args}, self.kwargs={self.kwargs}')
            scoreList.append(np.nanmean(tmp_score))
                
        # scoreList = [self.ProcessFunction(np.squeeze(chunk), *self.args, **self.kwargs) for chunk in dataChunks]
        # print(f'scoreList={scoreList}')
        # Finally, extract y limits
        self.cal = (np.min(scoreList), np.max(scoreList), np.mean(scoreList))
        self.BlocksProcessed = blockMemory[-1]
        self.dataPerBlock = self.blockDurS  * self.sr
        print("\t...done.")

    def update(self):
        ''' Process new data 
        Parameters:
        -----------
        dataMemory : list/numpy.ndarray, array of data points of a single 
        blockMemory : ist/numpy.ndarray, array of block indices
        '''
        dataMemory = self.gatherer.dataMemory
        blockMemory = self.gatherer.blockMemory
        # Check if Neurofeedback has been calibrated:
        if self.cal is None:
            self.calibrate(dataMemory, blockMemory)
            if self.cal is None:
                time.sleep(1)
                return (False, False)
        # Get dataMemory in consistent shape
        dataMemory = self.handleDataInput(dataMemory)
        # Calculate properties of the data (e.g. sampling rate)
        self.calculate_data_properties(dataMemory, blockMemory)
        if blockMemory[-1] < (self.BlocksProcessed + self.minNumberOfBlocks):
            # not enough data blocks available to start next processing
            time.sleep(self.timeRangeProcessed)  # sleep a bit
            return (False, False)
        # Extract data
        currentData = self.extract_current_data(dataMemory, blockMemory)
        # Calculate Neurofeedback Score
        score = []
        # Call ProcessFunction for each channel of interest
        for i in range(currentData.shape[0]):
            tmp_score = self.ProcessFunction(currentData[i, :], *self.args, **self.kwargs)
            score.append( tmp_score )
        
        if len(score) == 1:
            score = score[0]
        else:
            # Average over all channels available
            score = np.mean(score)
        
        # Retrieve average value across scoreMemory
        self.scoreMemory[0:-1] = self.scoreMemory[1:]
        self.scoreMemory[-1] = score
        scoreHysteresis = np.nanmean(self.scoreMemory)
        
        self.BlocksProcessed = blockMemory[-1]
        
        result = (self.canvas, scoreHysteresis, self.cal)

        return (True, result)

    def extract_current_data(self, dataMemory, blockMemory):
        blockMemory = list(blockMemory)
        newBlocks = (int(self.BlocksProcessed), int(blockMemory[-1]))
        newBlocksIndices = (blockMemory.index(newBlocks[0]), blockMemory.index(newBlocks[1]))
        dataMemoryIndices = (int(round(newBlocksIndices[0] * self.dataPerBlock)), int(round(newBlocksIndices[1] * self.dataPerBlock)))
        currentData = dataMemory[self.indicesOfInterest, dataMemoryIndices[0]:dataMemoryIndices[1]]
        return currentData

    def calculate_data_properties(self, dataMemory, blockMemory):
        if not hasattr(self, "sr"):
            self.sr = (dataMemory.shape[1] / len(blockMemory)) / self.blockDurS
            self.blockSize = self.blockDurS * self.sr
            self.numberOfElectrodes = dataMemory.shape[0]
            if self.indicesOfInterest is None:
                self.indicesOfInterest = np.arange(self.numberOfElectrodes)
    
    @staticmethod
    def handleDataInput(dataMemory):
        ''' Re-configures the dataMemory input to fulfill the following conditions:
        * must be of type numpy.ndarray
        * must be of dimension 2: channels X time points
        Parameters:
        -----------
        dataMemory : list/numpy.ndarray of data points
        
        Return:
        -------
        dataMemory : 2D numpy.ndarray
        '''

        if type(dataMemory) == list:
            dataMemory = np.array(dataMemory)
        if len(dataMemory.shape) == 1:
            dataMemory = np.expand_dims(dataMemory, axis=0)
        
        return dataMemory

    def set_animation(self, animation):
        self.canvas.ax.clear()
        self.NF_worker.signals.result.connect(animation)
        