from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg

import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather, DummyGather
from plot import DataMonitor, HistMonitor, BaseNeuroFeedback
from gui import *
from util import calc_error, gradient_descent, freq_band_power
from communication import StimulusCommunication
import time
import numpy as np
import os
import json
import random
from workers import *
from copy import deepcopy
from scipy.signal import detrend

class Octopus(MainWindow):
    def __init__(self):
        ''' Meta class that handles data collection, plotting and actions of the 
            SCP Libet Neurofeedback Experiment.
        '''
        super(Octopus, self).__init__()
        # Initialize callbacks
        self.callbacks = Callbacks(self)
        # Open Settings GUI
        self.open_settings_gui()
        
        # Misc attributes
        self.threadpool = QThreadPool()
        self.targetMarker = 'response'
        self.communicate_quit_code = 2
        self.EOGCorrectionDuration = 10
        self.d_est = np.zeros(100)
        self.responded = False
        self.current_state = 0
        self.get_statelist()
        self.quit = False
        print('Initialized Octopus')
    
    def open_settings_gui(self):
        self.mydialog = InputDialog(self)
        self.mydialog.show()
    
    def saveSettings(self, settings):
        ''' Save the settings entered by the User on startup of the program.'''
        self.SubjectID = settings['SubjectID']
        self.channelOfInterestName = settings['channelOfInterestName']
        self.viewChannel = deepcopy(self.channelOfInterestName)
        self.refChannels = ["".join(s.split()) for s in settings['refChannels'].split(',')]
        self.EOGChannelName = settings['EOGChannelName']
        self.SCPTrialDuration = float(settings['SCPTrialDuration'])
        self.SCPBaselineDuration = float(settings['SCPBaselineDuration'])
        self.samplingCrit = int(settings['samplingCrit'])
        self.secondInterviewDelay = int(settings['secondInterviewDelay'])
        self.blindedAxis = bool(settings['blindedAxis'])
        
    def setBlinding(self):
        # blinding
        if self.blindedAxis:
            # Blind Plots by randomly inverting amplitudes
            self.blinder = np.random.choice([-1, 1], 1)[0]
        else:
            # No blinding
            self.blinder = 1

    def run(self, settings):
        ''' When settings are entered, save them in the octopus.'''
        # Save the settings
        self.saveSettings(settings)
        # Set Blinding
        self.setBlinding()
        
        # Add title to datamonitor plot
        title = f"EEG: {self.channelOfInterestName}"
        self.graphWidget1.setTitle(title, color="k", size="10pt")
        
        # Load subject data in case of a crash
        self.load()
        
        self.read_blinded_conditions()

        # Objects 
        self.gatherer = DummyGather() # Gather()
        self.callbacks.connectRDA()
        self.internal_tcp = StimulusCommunication(self)
        
        # Data Monitors
        self.plotsReady = False
        self.init_plots()

        # Set timer for GUI-related tasks:
        self.timer = QTimer()
        self.timer.setInterval(100)  # every 100 ms it is called
        self.timer.timeout.connect(self.GUI_routines)
        self.timer.start()
        
        self.plotTimer = QTimer()
        self.plotTimer.setInterval(10)  # every 10 ms it is called
        self.plotTimer.timeout.connect(self.data_monitor_update)
        self.plotTimer.start()

        # Threading:
        self.worker_gatherer = Worker(self.gatherer.gather_data)
        self.worker_communication = SignallingWorker(self.internal_tcp.communication_routines)
        self.worker_communication.signals.result.connect(self.response_triggered)  
        
        
        self.threadpool.start(self.worker_gatherer)
        self.threadpool.start(self.worker_communication)
        
    def init_plots(self):
        ''' Start Data and Histogram Monitor: '''
        if not hasattr(self, 'gatherer'):
            self.plotsReady = False
            return
        if not hasattr(self, 'internal_tcp'):
            self.plotsReady = False
            return

        if self.gatherer.connected:
            self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, 
                curve=self.curve1, widget=self.graphWidget1, title=self.title, 
                viewChannel=self.viewChannel, EOGChannelIndex=self.EOGChannelIndex,
                blinder=self.blinder)
            
            self.hist_monitor = HistMonitor(self.gatherer.sr, canvas=self.MplCanvas, 
                SCPTrialDuration=self.SCPTrialDuration, 
                channelOfInterestIdx=self.channelOfInterestIdx,
                EOGChannelIndex=self.EOGChannelIndex, blinder=self.blinder)

            # self.startNeurofeedbacks()
            self.plotsReady = True
        else:
            self.plotsReady = False

    def data_monitor_update(self):
        if self.plotsReady:
            self.data_monitor.update(self.gatherer, self.d_est, self.viewChannel)
    
    def fillChannelDropdown(self):
        ''' Fill the channel dropdown menu with channel names yielded from the gatherer.'''
        for channelname in self.gatherer.channelNames:
            self.channel_dropdown.addItem(channelname)
            
    def GUI_routines(self):
        ''' Routines that are called using a timer ''' 
        if self.plotsReady:
            self.save()
            self.checkState()
        else:
            self.init_plots()

    def response_triggered(self, result):
        ''' This function is called whenever the participant presses the button.'''
        if result:
            self.hist_monitor.button_press(self.gatherer, self.d_est)
            self.hist_monitor.plot_hist()

    def checkState(self, recent_response=False):
        ''' This method specifies the logic of the experiment.
            States are listed in get_statelist().
        '''
        # print('Checking state')
        if recent_response and (self.current_state == 1 or self.current_state == 3):
            self.check_if_interview()
            if self.go_interview:
                self.current_state += 1
                self.callbacks.presentToggle()
                
        if self.current_state == 0 and len(self.hist_monitor.scpAveragesList) >= self.samplingCrit:
            self.current_state = 1
            self.hist_monitor.current_state = self.current_state
            # self.textbox.statusBox.set_text(f"State={self.current_state}")
        
        if (self.current_state == 2 or self.current_state == 4) and self.callbacks.allow_presentation:
            # Interview must be over
            print("Interview is over, lets continue!")
            self.current_state += 1

        if self.current_state == 5 or self.callbacks.quit == True:
            self.closeAll()

        self.textBox.setText(f"State={self.current_state}\n{self.stateDescription[self.current_state]}")
        
    def check_if_interview(self):
        
        n_scps = len(self.hist_monitor.scpAveragesList)

        if n_scps < self.samplingCrit:
            print("Too few SCPs in list.")
            self.go_interview = False
            return

        last_scp = self.hist_monitor.scpAveragesList[-1]
        avg_scp = np.median(self.hist_monitor.scpAveragesList)
        sd_scp = np.std(self.hist_monitor.scpAveragesList)

        self.go_interview = False

        # if we are right before first interview:
        if self.current_state == 1:
            # Check in which condition we are:
            key = self.cond_order[0]
            condition = self.conds[key]

            if condition == 'Positive':
                self.go_interview = (last_scp > avg_scp + sd_scp) and (last_scp > 0)
            elif condition == 'Negative':
                self.go_interview = (last_scp < avg_scp - sd_scp) and (last_scp < 0)

            # Save how many trials it took until the first interview was started
            self.trials_until_first_interview = n_scps

        # if we are right before second interview:
        elif self.current_state == 3:
            key = self.cond_order[1]
            condition = self.conds[key]
            # Make sure there were some trials between the first and the second interview
            # using the "secondInterviewDelay" variable.
            if n_scps < self.trials_until_first_interview + self.secondInterviewDelay:
                self.go_interview = False
            else:
                if condition == 'Positive':
                    self.go_interview = (last_scp > avg_scp + sd_scp) and (last_scp > 0)
                elif condition == 'Negative':
                    self.go_interview = (last_scp < avg_scp - sd_scp) and (last_scp < 0)

        if not self.go_interview and n_scps < self.samplingCrit:
            print("Too few trials to start interview.")
        if not self.go_interview and n_scps >= self.samplingCrit:
            print("SCP not large enough to start interview.")
        
    def get_statelist(self):
        ''' Here the number and description of states will be defined.
        '''
        self.stateDescription = ["Waiting for more data.",
            "Waiting for appropriate SCP of first condition.",
            "Interview for first condition.",
            "Waiting for appropriate SCP of second condition.",
            "Interview for second condition.",
            "Quit Experiment."
            ]

    def read_blinded_conditions(self):
        ''' This method reads a json file called blinding.txt that contains the assignment 
            between the conditions (Positive & Negative) and some blinding labels (A & B).
            This assignment is stored in a dictionary and the condition order will be defined
            randomized by shuffling.
        '''
        if not hasattr(self, 'cond_order'):
            filename = "blinding.txt"
            assert os.path.isfile(filename), 'json file called {} needs to be present for proper blinding.'.format(filename)
            # Read json
            with open('blinding.txt', 'r') as infile:
                json_text_read = json.load(infile)
            # Json to python dictionary
            self.conds = json.loads(json_text_read)
            # Shuffle order of conditions
            self.cond_order = [key for key in self.conds.keys()]
            random.shuffle(self.cond_order)
    
    def handleChannelIndex(self):
        # Handle the requested channel name in case of wrong 
        # spelling or workspace
        try:
            self.channelOfInterestIdx = self.gatherer.channelNames.index(self.channelOfInterestName)
            self.EOGChannelIndex = self.gatherer.channelNames.index(self.EOGChannelName)
        except ValueError:
            print(f"Channel name {self.channelOfInterestName} is not in the list of channels ({self.gatherer.channelNames})")
            print('Opening Gui again')
            self.open_settings_gui()

    def save(self):
        ''' Save the current state of the experiment. 
        (not finished)
        '''
        # print('saving')
        if not os.path.isdir('states/'):
            # If there is no folder to store states in -> create it
            os.mkdir('states/')

        State = {'scpAveragesList': list(self.hist_monitor.scpAveragesList), 
                'current_state':int(self.current_state), 
                'SubjectID': self.SubjectID,
                'cond_order': self.cond_order,
                'd_est': list(self.d_est)}

        json_file = json.dumps(State)

        filename = "states/" + self.SubjectID + '.json'
        with open(filename, 'w') as f:
            json.dump(json_file, f)
            
    def load(self):
        ''' Check if subject is already in folder and ask whether the data should be loaded.'''
            
        filename = "states/" + self.SubjectID + '.json'
        if not os.path.isfile(filename):
            print("This is a new participant.")
        else:
            answer = input(f"ID {self.SubjectID} already exists. Load data? [Y/N] ")
            if answer == "Y":
                with open(filename, 'r') as f:
                    json_file_read = json.load(f)
                
                State = json.loads(json_file_read)

                self.hist_monitor.scpAveragesList = State['scpAveragesList']
                self.current_state = State['current_state']
                self.SubjectID = State['SubjectID']
                self.cond_order = State['cond_order']
                self.d_est = State['d_est']
            elif answer == "N":
                self.save()
            else:
                self.load()

    def closeAll(self):
        # Save experiment
        print("stopping")
        self.save()
        # close routines
        self.plotTimer.stop()
        self.timer.stop()
        self.internal_tcp.quit()
        self.gatherer.quit()
        # Quit experiment
        self.quit = True
        # self.internal_tcp.quit()
        self.close()
        # print(f'Quitted. self.internal_tcp.con.fileno()={self.internal_tcp.con.fileno()}')

    def EOGcorrection(self, name_eog):
        # 1) Record Data for 10 seconds
        data = self.record_data(self.EOGCorrectionDuration)
        # 2) Select EOG and channel of interest
        idx_eog = self.gatherer.channelNames.index(name_eog)
        print(f"name of selected EOG channel: {name_eog}, idx={idx_eog}")
        EOG = data[idx_eog, :]

        # 3) Detrend signals
        EOG = detrend(EOG)  # try to eliminate drifts etc

        # 4) Calculate ratio of rms between EOG and other channels
        from util import rms
        rms_eog = rms(EOG)
        rms_chans = [rms(dat) for i, dat in enumerate(data)]
        
        amplitudeRatios = [rms_chan / rms_eog for rms_chan in rms_chans]

        # 5) Estimate 'd' for each channel separately using individual scalings
        print('\tCalc d...')
        d_est = []
        for idx in range(data.shape[0]):
            scaler = amplitudeRatios[idx]
            tmp_d_est = gradient_descent(calc_error, EOG*scaler, data[idx, :])
            tmp_d_est *= scaler
            d_est.append(tmp_d_est)
        
        self.d_est = d_est
        print('\t\t...done.')
        return (data, idx_eog)

    def record_data(self, nsec):
        print('\tRecording...')
        time.sleep(nsec)
        print('\t\t...done.')
        return self.gatherer.dataMemory

    def plot_eog_results(self, results):
        print("\t...done.")
        data, idx_eog = results
        EOG = data[idx_eog, :]
        
        print(f'channelOfInterestIdx={self.channelOfInterestIdx}; self.channelOfInterestName={self.channelOfInterestName}')
        COI = data[self.channelOfInterestIdx, :]
        d = self.d_est[self.channelOfInterestIdx]
        plt.figure(num=42)
        plt.subplot(311)
        plt.plot(EOG)
        plt.title("EOG")
        plt.subplot(312)
        plt.plot(COI)
        plt.title(f"Channel of interest ({self.channelOfInterestName})")
        plt.subplot(313)
        plt.plot(COI - (EOG * d))
        title = f"Cleaned channel of interest with d={d:.2f}"
        plt.title(title)
        plt.tight_layout(pad=2)
        plt.show()
    
    def startNeurofeedbacks(self):
        channelsOfInterest = ['Cz']
        indicesOfInterest = [self.gatherer.channelNames.index(chan) for chan in channelsOfInterest]
        freqs = (8, 13)  # low and high frequency for the bandpass filter
        sr = self.gatherer.sr
        self.NF_alpha = BaseNeuroFeedback(freq_band_power, freqs, sr, timeRangeProcessed=0.25, 
            blocksPerSecond=self.gatherer.blocks_per_s, indicesOfInterest=indicesOfInterest)
        
        self.NF_worker = SignallingWorker(self.update_alpha_neurofeedback)
        self.NF_worker.signals.result.connect(self.plotFreqBandNeurofeedback)  
        self.threadpool.start(self.NF_worker)

    def update_alpha_neurofeedback(self):
        result = self.NF_alpha.update(self.gatherer.dataMemory, self.gatherer.blockMemory)
        return result

    def plotFreqBandNeurofeedback(self, result):
        # plot the frequency band power on a canvas
        score, ylim = result
        
        self.barGraph.ax.cla()

        self.hist = self.barGraph.ax.bar(0, score)   
        self.barGraph.ax.set_xlabel('Alpha Power')
        self.barGraph.ax.set_ylim(ylim)        



