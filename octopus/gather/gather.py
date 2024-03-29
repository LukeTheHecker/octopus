import socket
from struct import unpack
import numpy as np
import time
from  octopus import util

class Gather:
    def __init__(self, port=51244, sockettimeout=0.1):
        ''' 
        Parameters:
        -----------
        ip : str, IP adress of the PC that sends remote data access (RDA) of the brain 
            vision recorder software
        port : int, corresponding port (see above)
        plot_interval : int/float, interval in seconds in which to update data stream plot
            (affects DataMonitor class, method: .update())
        targetMarker : str, marker of button press (deprecated)

        '''

        # Data handling
        self.blocks_per_s = 50
        self.block_counter = 0
        self.dataMemoryDurS = 10  # seconds of data memory
        self.block_dur_s = 1.0/self.blocks_per_s
        self.blockSize = None
        self.sr = None

        # Preprocessing
        self.refChannels = None
        # Here the block number will be assigned to each piece of data in dataMemory
        self.blockMemory = np.array([-1] * self.blocks_per_s * self.dataMemoryDurS)
        self.startTime = None
        self.lag_s = None
        self.lastBlock = -1
        self.first_block_ever = None
        self.markerMemory = []

        # Data TCP Connection (with PC that sends RDA)
        self.connected = False
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.sockettimeout = sockettimeout
        self.retryText = ('Try again?', 'Connection to Remote Data Access could not be established.')
        self.connect()
    
    def connect(self):
        ''' If connection failed it will prompt a dialog 
            to attempt it again.'''


        print(f'Attempting connection to RDA {self.ip} {self.port}...')
        self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.con.settimeout(self.sockettimeout)

        try:
            self.con.connect((self.ip, self.port))
            self.connected = True
            # Perform main loop until parameters like sr are there.
            while self.blockSize is None or self.sr is None:
                self.main()
                
            if self.blockSize is None or self.sr is None:
                print('\t...failed.')
                self.connected = False
                return False
            print('\t...done.')
            return True
        except:
            pass

        self.connected = False
        print('\t...failed.')
        return False
            # gui_retry_cancel(self.connect, self.retryText)
        
    def fresh_init(self):
        ''' Re-Do connection right before experiment.'''
        self.blockMemory = np.array([-1] * self.blocks_per_s * self.dataMemoryDurS)
        self.block_counter = 0
        self.dataMemory = np.empty((self.channelCount, self.dataMemorySize))
        self.dataMemory[:] = np.nan

        # Close connection if there is one at all:
        if hasattr(self, 'con'):
            if self.connected:
                self.con.close()            
        self.connect()
        # self.startTime = time.time()
       
    def main(self):
        ''' Get data from Brain Vision RDA'''
        if not self.connected:
            return
        try:
            # Get message header as raw array of chars
            self.rawhdr = self.RecvData(24)

            # Split array into usefull information id1 to id4 are constants
            (id1, id2, id3, id4, msgsize, msgtype) = unpack('<llllLL', self.rawhdr)#.encode('utf-8', "replace"))

            # Get data part of message, which is of variable size
            self.rawdata = self.RecvData(msgsize - 24)

            # Perform action dependend on the message type
            if msgtype == 1:
                # Start message, extract eeg properties and display them
                self.GetProperties()
                # reset block counter
                self.lastBlock = -1
                print('#########################')
                print("Starting Data Acquisition")
                print("Number of channels: " + str(self.channelCount))
                print("Sampling interval: " + str(self.samplingInterval))
                print("Resolutions: " + str(self.resolutions))
                print("Channel Names: " + str(self.channelNames))
                print('#########################')
                print('\n')

                # Calculate some important values:
                self.sr = int(1000 / (self.samplingInterval / 1000))  # Sampling rate
                self.blockSize = int(self.block_dur_s * self.sr)  # data points per block
                self.theoreticalLooptime = float(self.blockSize) / self.sr

                self.dataMemorySize = self.dataMemoryDurS * self.blocks_per_s * self.blockSize  # number of data points in memory
                self.dataMemory = np.empty((self.channelCount, self.dataMemorySize))
                self.dataMemory[:] = np.nan

                self.data = np.array([np.nan] * int(self.blockSize))

            elif msgtype == 4:
                # Data message, extract data and markers
                self.GetData()
                
                # Check for overflow
                if self.lastBlock != -1 and self.block > self.lastBlock + 1:
                    print("*** Overflow with " + str(self.block - self.lastBlock) + " datablocks ***" )
                self.lastBlock = self.block

                # Lag Calculation        
                if self.startTime is not None:
                    endTime = time.time()
                    measuredLoopTime = endTime - self.startTime
                    calculatedEndTime = (self.theoreticalLooptime*(self.block-self.first_block_ever))  # (self.block_counter+1))
                    self.lag_s = calculatedEndTime - measuredLoopTime
                    # if self.lag_s > 0.05:
                    #     print(self.lag_s)

            elif msgtype == 3:
                # Stop message, terminate program
                print("Stop")
                self.quit()
        except OSError as err:
            print("Connection probably closed")
            self.connected = False
   
    def gather_data(self):
        if not self.connected:
            # If connection to Remote Data Access was not established yet
            print("Gatherer is not connected.")
            return
        self.fresh_init()
        while self.connected:
            # start = time.time()*1000
            self.main()
            # end = time.time()*1000
            # print(f"time elapsed: {end-start:.1f} ms")
            # time.sleep(0.05)
        # self.quit()

    def RecvData(self, requestedSize):
        ''' Helper function for receiving whole message.'''
        returnStream = bytearray()#''

        while len(returnStream) < requestedSize:
            databytes = self.con.recv(requestedSize - len(returnStream))

            if str(databytes.decode('utf8', "replace")) == '':
                raise RuntimeError("connection broken")
            returnStream += databytes
        return returnStream   
    
    @staticmethod
    def SplitString(raw):
        ''' Helper function for splitting a raw array of
            zero terminated strings (C) into an array of python strings'''
        stringlist = []
        s = ""
        raw = raw.decode('utf-8')
        for i in range(len(raw)):
            if raw[i] != '\x00':
                s = s + raw[i]
            else:
                stringlist.append(s)
                s = ""

        return stringlist

    def GetProperties(self):
        ''' Helper function for extracting eeg properties from a raw data array
            read from TCP IP socket'''
        # Extract numerical data
        (self.channelCount, self.samplingInterval) = unpack('<Ld', self.rawdata[:12])

        # Extract resolutions
        self.resolutions = []
        for c in range(self.channelCount):
            index = 12 + c * 8
            restuple = unpack('<d', self.rawdata[index:index+8])
            self.resolutions.append(restuple[0])

        # Extract channel names
        self.channelNames = self.SplitString(self.rawdata[12 + 8 * self.channelCount:])

        # return (channelCount, samplingInterval, resolutions, channelNames)
  
    def GetData(self):
        ''' Helper function for extracting eeg and marker data from a raw data array
            read from tcpip socket '''
        # Extract numerical data
        (self.block, self.points, self.markerCount) = unpack('<LLL', self.rawdata[:12])

        if self.first_block_ever is None:
            self.first_block_ever = self.block
            self.startTime = time.time()

        # Extract eeg data as array of floats
        self.old_data = self.data.copy()
        self.data = []

        for i in range(self.points * self.channelCount):
            index = 12 + 4 * i
            value = unpack('<f', self.rawdata[index:index+4])
            self.data.append(value[0])

        self.new_data = [list() for _ in range(self.channelCount)]

        # reshape into chan x timepoints
        chan_idx = np.arange(len(self.data)) % self.channelCount

        for i, dat in enumerate(self.data):
            self.new_data[chan_idx[i]].append(dat)
        self.data = np.array(self.new_data)
        # Preprocessing (rereferencing, ...)
        self.preprocess_data()

        # print(self.data)
        # print(self.data.shape)
        # print(f'self.data = {self.data}, len={len(self.data)}')
        # self.data = np.array(self.data).reshape(self.channelCount, int(len(self.data)/self.channelCount))
        
        # value = value / self.channelCount
        self.block_counter += 1
        self.update_data()
        try:
            if self.data == self.old_data:
                print("Its a copy")
        except:
            pass

        # Extract markers
        self.markers = []
        index = 12 + 4 * self.points * self.channelCount
        for m in range(self.markerCount):
            markersize = unpack('<L', self.rawdata[index:index+4])

            ma = Marker()
            (ma.position, ma.points, ma.channel) = unpack('<LLl', self.rawdata[index+4:index+16])
            typedesc = self.SplitString(self.rawdata[index+16:index+markersize[0]])
            ma.type = typedesc[0]
            ma.description = typedesc[1]

            self.markers.append(ma)
            index = index + markersize[0]

        # return (self.block, self.points, self.markerCount, self.data, self.markers)
        if len(self.markers)>0:
            if self.markers[0].description == "S 10":
                self.markerMemory.extend(self.markers)
            
    def preprocess_data(self):
        non_eeg_channels = ['veog', 'res', 'resp', 'respiration']
        
        # rereferencing
        # if self.refChannels is not None:
        #     self.refChannelsIndices = [self.channelNames.index(i) for i in self.refChannels]
        #     # loop through channels
        #     for i in range(self.data.shape[0]):
        #         if any([elem == self.channelNames[i].lower() for elem in non_eeg_channels]):
        #             continue
        #         self.data[i, :] -= np.mean(self.data[self.refChannelsIndices, :], axis=0)
        #         print("Subtracting shape: ", np.mean(self.data[self.refChannelsIndices, :], axis=0).shape, " from ", self.data[i,:].shape)


    def update_data(self):
        ''' Collect new data and add it to the data memory.
        Parameters:
        -----------
        data_package : numpy.ndarray/list, new data retrieved from rda.
        '''
        if self.blockSize is None:
            self.blockSize = len(self.data)

        assert self.blockSize == len(self.data.flatten()) / self.channelCount, "blockSize is supposed to be {} but data was of size {}".format(self.blockSize, len(self.data))
        self.dataMemory = util.insert(self.dataMemory, self.data)
        self.blockMemory = util.insert(self.blockMemory, self.block_counter)
        self.blockMemory = np.squeeze(self.blockMemory)

    def quit(self):
        self.con.close()
        self.connected = False


class DummyGather:
    def __init__(self, port=51244, targetMarker='response',
        sockettimeout=0.1):
        ''' 
        Parameters:
        -----------
        ip : str, IP adress of the PC that sends remote data access (RDA) of the brain 
            vision recorder software
        port : int, corresponding port (see above)
        plot_interval : int/float, interval in seconds in which to update data stream plot
            (affects DataMonitor class, method: .update())
        targetMarker : str, marker of button press (deprecated)

        '''

        # Data handling
        self.blocks_per_s = 50
        self.block_counter = 0
        self.dataMemoryDurS = 10  # seconds of data memory
        self.block_dur_s = 1.0/self.blocks_per_s
        self.blockSize = None
        self.sr = None

        # Preprocessing
        self.refChannels = None
        # Here the block number will be assigned to each piece of data in dataMemory
        self.blockMemory = np.array([-1] * self.blocks_per_s * self.dataMemoryDurS)
        self.startTime = None
        self.lag_s = None
        self.first_block_ever = None

        # Data TCP Connection (with PC that sends RDA)
        self.connected = False
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.sockettimeout = sockettimeout
        self.retryText = ('Try again?', 'Connection to Remote Data Access could not be established.')
        
        # Calculate some important values:
        self.GetProperties()
        # reset block counter
        self.lastBlock = -1

        self.sr = int(1000 / (self.samplingInterval / 1000))  # Sampling rate
        self.blockSize = int(self.block_dur_s * self.sr)  # data points per block
        self.theoreticalLooptime = float(self.blockSize) / self.sr

        self.dataMemorySize = self.dataMemoryDurS * self.blocks_per_s * self.blockSize  # number of data points in memory
        self.dataMemory = np.empty((self.channelCount, self.dataMemorySize))
        self.dataMemory[:] = np.nan

        self.data = np.array([np.nan] * int(self.blockSize))
        self.d = 0.5
        self.connect()
        
    
    def connect(self):
        ''' If connection failed it will prompt a dialog 
            to attempt it again.'''

        self.con = DummyCon()
        self.connected = True
        print(f'Dummy connection established')
        return True
        
    
    def fresh_init(self):
        ''' Re-Do connection right before experiment.'''
        self.blockMemory = np.array([-1] * self.blocks_per_s * self.dataMemoryDurS)
        self.block_counter = 0
        self.dataMemory = np.empty((self.channelCount, self.dataMemorySize))
        self.dataMemory[:] = np.nan
        self.startTime = time.time()
       
    def main(self):
        ''' Get data from Brain Vision RDA'''
        if not self.connected:
            return
        # Create Data and all that
        start = time.time()
        self.GetData()
        # Lag Calculation        
        if self.startTime is not None:
            endTime = time.time()
            measuredLoopTime = endTime - self.startTime
            calculatedEndTime = (self.theoreticalLooptime*(self.block-self.first_block_ever))  # (self.block_counter+1))
            self.lag_s = calculatedEndTime - measuredLoopTime
            

        # wait a bit for next block of dummy data
        end = time.time()
        elapsed = end - start
        time.sleep(np.clip((1/self.blocks_per_s) - elapsed, a_min=0, a_max=99999))
   
    def gather_data(self):
        if not self.connected:
            # If connection to Remote Data Access was not established yet
            print("Gatherer is not connected.")
            time.sleep(0.25)
            return
        self.fresh_init()
        while self.connected:
            self.main()
        self.quit()

    def RecvData(self, requestedSize):
        ''' Helper function for receiving whole message.'''
        returnStream = bytearray()#''

        while len(returnStream) < requestedSize:
            databytes = self.con.recv(requestedSize - len(returnStream))

            if str(databytes.decode('utf8', "replace")) == '':
                raise RuntimeError("connection broken")
            returnStream += databytes
        return returnStream   
    
    @staticmethod
    def SplitString(raw):
        ''' Helper function for splitting a raw array of
            zero terminated strings (C) into an array of python strings'''
        stringlist = []
        s = ""
        raw = raw.decode('utf-8')
        for i in range(len(raw)):
            if raw[i] != '\x00':
                s = s + raw[i]
            else:
                stringlist.append(s)
                s = ""

        return stringlist

    def GetProperties(self):
        ''' Helper function for extracting eeg properties from a raw data array
            read from TCP IP socket'''
        # Define channel names
        self.channelNames = ['Cz', 'leftBrain', 'rightBrain', 'centerOfConsciousness', 'TP9', 'TP10', 'VEOG']
        # Define numerical data
        (self.channelCount, self.samplingInterval) = [len(self.channelNames), 1000]

        # Extract resolutions
        self.resolutions = [0.01] * self.channelCount
  
    def GetData(self):
        ''' Helper function for extracting eeg and marker data from a raw data array
            read from tcpip socket '''
        # Extract numerical data
        (self.block, self.points, self.markerCount) = (self.block_counter, self.blockSize, 0)

        if self.first_block_ever is None:
            self.first_block_ever = self.block
            self.startTime = time.time()

        # Extract eeg data as array of floats
        self.data = np.cumsum(np.random.randn(self.channelCount, self.blockSize), axis=1)
        for i in range(self.channelCount):
            self.data[i, :] = np.cumsum(self.data[i, :])
        # Preprocessing (rereferencing, ...)
        self.preprocess_data()

        # Some stochastically ocurring eye artifacts
        if np.random.rand(1) < 0.05:
            eog_idx = self.channelNames.index('VEOG')
            self.data[eog_idx, :] = util.pulse(self.blockSize) * 50
            for i in range(self.channelCount):
                if i != eog_idx:
                    self.data[i, :] += self.data[eog_idx, :] * self.d
        
        self.block_counter += 1
        self.update_data()
    
    def preprocess_data(self):
        # rereferencing
        if self.refChannels is not None:
            self.refChannelsIndices = [self.channelNames.index(i) for i in self.refChannels]
            # loop through channels
            for i in range(self.data.shape[0]):
                if self.channelNames[i] == 'VEOG':
                    continue
                self.data[i, :] -= np.mean(self.data[self.refChannelsIndices, :], axis=0)

    def update_data(self):
        ''' Collect new data and add it to the data memory.
        Parameters:
        -----------
        data_package : numpy.ndarray/list, new data retrieved from rda.
        '''
        if self.blockSize is None:
            self.blockSize = len(self.data)

        assert self.blockSize == len(self.data.flatten()) / self.channelCount, "blockSize is supposed to be {} but data was of size {}".format(self.blockSize, len(self.data))
        self.dataMemory = util.insert(self.dataMemory, self.data)
        self.blockMemory = util.insert(self.blockMemory, self.block_counter)
        self.blockMemory = np.squeeze(self.blockMemory)

    def quit(self):
        self.con.close()
        self.connected = False

class Marker:
    ''' Little helper class to extract markers from Brain Vision Amp'''
    def __init__(self):
        self.position = 0
        self.points = 0
        self.channel = -1
        self.type = ""
        self.description = ""
    
    def pprint(self):
        print(
            "Position: ", self.position,
            "\nPoints: ", self.points,
            "\nChannel: ", self.channel,
            "\nType: ", self.type,
            "\nDescription: ", self.description,
        )

class DummyCon:
    def __init__(self):
        self.connected = False

    def close(self):
        self.connected = False


