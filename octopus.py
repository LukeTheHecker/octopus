from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg

import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor
from gui import *
from communication import StimulusCommunication
import time
import numpy as np
import os
import json
import random
from workers import Worker, SignallingWorker

class Octopus(QMainWindow, MainWindow):
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
        self.targetMarker = 'response'
        self.communicate_quit_code = 2
        self.responded = False
        self.current_state = 0
        self.get_statelist()
        self.quit = False
        print('Initialized Octopus')
    
    def open_settings_gui(self):
        self.mydialog = InputDialog(self)
        self.mydialog.show()
        # self.SubjectID = input("Enter ID: ") 
    
    def run(self, settings):
        ''' When settings are entered, save them in the octopus.'''
        # Handle Inputs
        self.SubjectID = settings['SubjectID']
        self.channelOfInterestName = settings['channelOfInterestName']
        self.SCPTrialDuration = float(settings['SCPTrialDuration'])
        self.SCPBaselineDuration = float(settings['SCPBaselineDuration'])
        self.histCrit = int(settings['histCrit'])
        self.secondInterviewDelay = int(settings['secondInterviewDelay'])
        self.blindedAxis = bool(settings['blindedAxis'])

        # Add title to datamonitor plot
        title = f"EEG: {self.channelOfInterestName}"
        self.graphWidget1.setTitle(title, color="k", size="10pt")
        # blinding
        if self.blindedAxis:
            # Blind Plots by randomly inverting amplitudes
            self.blinder = np.random.choice([-1, 1], 1)[0]
        else:
            # No blinding
            self.blinder = 1
        print("settings saved to octopus")

        # Load subject data in case of a crash
        self.load()
        
        self.read_blinded_conditions()

        # Objects 
        self.gatherer = Gather()
        # self.gatherer.connect()
        self.callbacks.connectRDA()
        self.internal_tcp = StimulusCommunication(self)
        
        

        # Data Monitors
        self.plotsReady = False
        self.init_plots()

        # Set timer for GUI-related tasks:
        self.timer = QTimer()
        self.timer.setInterval(100)  # every 50 ms it is called
        self.timer.timeout.connect(self.GUI_routines)
        self.timer.start()
        
        self.plotTimer = QTimer()
        self.plotTimer.setInterval(10)  # every 50 ms it is called
        self.plotTimer.timeout.connect(self.data_monitor_update)
        self.plotTimer.start()

        # Threading:
        self.worker_gatherer = Worker(self.gatherer.gather_data)
        self.worker_communication = SignallingWorker(self.internal_tcp.communication_routines)

        self.threadpool = QThreadPool()
        self.threadpool.start(self.worker_gatherer)
        self.threadpool.start(self.worker_communication)
        self.worker_communication.signals.result.connect(self.response_triggered)  
    
    def init_plots(self):
        if self.gatherer.connected and self.internal_tcp.connected:
            self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, 
                curve=self.curve1, widget=self.graphWidget1, title=self.title, 
                channelOfInterestIdx=self.channelOfInterestIdx, blinder=self.blinder)
            
            self.hist_monitor = HistMonitor(self.gatherer.sr, canvas=self.MplCanvas, 
                SCPTrialDuration=self.SCPTrialDuration, histCrit=self.histCrit,
                channelOfInterestIdx=self.channelOfInterestIdx, blinder=self.blinder)
            self.plotsReady = True
        else:
            self.plotsReady = False

    def data_monitor_update(self):
        if self.plotsReady:
            self.data_monitor.update(self.gatherer)

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
            self.hist_monitor.button_press(self.gatherer)
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
                
        if self.current_state == 0 and len(self.hist_monitor.scpAveragesList) >= self.hist_monitor.histCrit:
            self.current_state = 1
            self.hist_monitor.current_state = self.current_state
            # self.textbox.statusBox.set_text(f"State={self.current_state}")
        
        if (self.current_state == 2 or self.current_state == 4) and self.callbacks.allow_presentation:
            # Interview must be over
            print("Interview is over, lets continue!")
            self.current_state += 1

        if self.current_state == 5 or self.callbacks.quit == True:
            # Save experiment
            #...
            self.internal_tcp.quit()
            # Quit experiment
            print("Quitting...")
            self.quit = True
            self.gatherer.quit()
            # self.internal_tcp.quit()
            self.close()
            # print(f'Quitted. self.internal_tcp.con.fileno()={self.internal_tcp.con.fileno()}')

        self.textBox.setText(f"State={self.current_state}\n{self.stateDescription[self.current_state]}")
        
    def check_if_interview(self):
        
        n_scps = len(self.hist_monitor.scpAveragesList)

        if n_scps < self.hist_monitor.histCrit:
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
                self.go_interview = last_scp > avg_scp + sd_scp
            elif condition == 'Negative':
                self.go_interview = last_scp < avg_scp - sd_scp

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
                    self.go_interview = last_scp > avg_scp + sd_scp
                elif condition == 'Negative':
                    self.go_interview = last_scp < avg_scp - sd_scp

        if not self.go_interview and n_scps < self.histCrit:
            print("Too few trials to start interview.")
        if not self.go_interview and n_scps >= self.histCrit:
            print("SCP not large enough to start interview.")
        
    def get_statelist(self):
        ''' Here the number and description of states will be defined.
        '''
        n_states = 6
        self.statelist = np.arange(n_states)
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
                'cond_order': self.cond_order}

        json_file = json.dumps(State)

        filename = "states/" + self.SubjectID + '.json'
        with open(filename, 'w') as f:
            json.dump(json_file, f)
            
    def load(self):
        if self.SubjectID != '':
            return
            
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
            elif answer == "N":
                self.save()
            else:
                self.load()




