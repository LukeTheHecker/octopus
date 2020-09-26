from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from plot import MplCanvas
import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor
from gui import *
from communication import TCP
import select
import time
import numpy as np
import os
import json
import random
from workers import Worker, SignallingWorker

class Octopus(QMainWindow):
    def __init__(self):
        ''' Meta class that handles data collection, plotting and actions of the 
            SCP Libet Neurofeedback Experiment.

        '''
        super(Octopus, self).__init__()

        # Get callbacks
        self.callbacks = Callbacks()
        # Set layout
        self.set_layout()
        # Open Settings:
        self.open_settings_gui()
        
        # Misc attributes
        self.targetMarker = 'response'
        self.communicate_quit_code = 2
        self.responded = False
        self.get_statelist()
        self.quit = False

        print('Initialized Octopus')
        
    def set_layout(self):
        # Layout stuff
        # Main Widget
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        # Icon
        self.setWindowIcon(QIcon('assets/octoicon.svg'))
        # label = QLabel(self)
        # pixmap = QPixmap('assets/octoicon.svg')
        # label.setPixmap(pixmap)

        # Title
        self.setWindowTitle('Octopus Neurofeedback')
        # Data monitor Graph
        self.graphWidget1 = pg.PlotWidget()
        
        pen = pg.mkPen(color='r', width=2)
        self.curve1 = self.graphWidget1.plot(pen=pen)
        
        # Styling
        # self.graphWidget1.plotItem.getAxis('left').setPen(pen)
        # self.graphWidget1.plotItem.getAxis('bottom').setPen(pen)
        # self.graphWidget1.setBackground((255, 255, 255))
        # self.curve1.setData([1, 2, 3], [3, 3, 2], width=0.1)
        # font=QFont("Times", 10)
        # font.setPixelSize(10)
        # self.graphWidget1.getAxis("bottom").setStyle(tickFont = font)
        # self.graphWidget1.getAxis("bottom").setStyle(tickTextOffset = 20)
        # labelstyle = {'color': (0, 0, 0), 'font-size': '14pt'}
        # self.graphWidget1.getAxis("bottom").setLabel("text", units='mV', **labelstyle)
        # self.graphWidget1.getAxis("left").setStyle(tickFont = font)
        # self.graphWidget1.getAxis("left").setStyle(tickTextOffset = 20)
        # Title
        self.title = QLabel()
        self.title.setText("Lag")
        self.title.setFont(QFont("Times", 12))
        # Bottom Graph
        self.MplCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add label
        self.textBox = QLabel()
        self.textBox.setText("State=")
        self.textBox.setFont(QFont("Times", 14))
        # Add buttons
        self.buttonPresentationcontrol = QPushButton("Allow")
        self.buttonPresentationcontrol.pressed.connect(self.callbacks.presentToggle)
        self.buttonPresentationcontrol.setStyleSheet("background-color: red")

        self.buttonQuit = QPushButton("Quit")
        self.buttonQuit.pressed.connect(self.callbacks.quitexperiment)

        self.buttonforward = QPushButton("->")
        self.buttonforward.pressed.connect(self.callbacks.stateforward)

        self.buttonbackwards = QPushButton("<-")
        self.buttonbackwards.pressed.connect(self.callbacks.statebackwards)
        
        # Layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.graphWidget1, 1,0, 2, 4)
        self.layout.addWidget(self.title, 0,0, 1, 1)
        self.layout.addWidget(self.MplCanvas, 3,0, 2, 4)
        self.layout.addWidget(self.textBox, 1, 4, 2,4)
        self.layout.addWidget(self.buttonPresentationcontrol, 2, 5, 1, 2)
        self.layout.addWidget(self.buttonQuit, 3, 7, 1, 1)
        self.layout.addWidget(self.buttonforward, 3, 6, 1, 1)
        self.layout.addWidget(self.buttonbackwards, 3, 5, 1, 1)
        # self.layout.addWidget(label, 4, 7, 1, 1)
  
        self.mainWidget.setLayout(self.layout)

    def init_plots(self):
        if self.gatherer.connected:
            self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, 
                curve=self.curve1, widget=self.graphWidget1, title=self.title, 
                channelOfInterestIdx=self.channelOfInterestIdx, blinder=self.blinder)
            
            self.hist_monitor = HistMonitor(self.gatherer.sr, canvas=self.MplCanvas, 
                SCPTrialDuration=self.SCPTrialDuration, histcrit=self.histcrit,
                channelOfInterestIdx=self.channelOfInterestIdx, blinder=self.blinder)
            self.plotsReady = True
        else:
            self.plotsReady = False
    
    def open_settings_gui(self):
        self.mydialog = InputDialog(self)
        self.mydialog.show()
        # self.SubjectID = input("Enter ID: ") 
    
    def insert_settings(self, settings):
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
        self.internal_tcp = TCP()
        
        # Handle the requested channel name in case of wrong 
        # spelling or workspace
        try:
            self.channelOfInterestIdx = self.gatherer.channelNames.index(self.channelOfInterestName)
        except ValueError:
            print(f"Channel name {self.channelOfInterestName} is not in the list of channels ({self.gatherer.channelNames})")
            print('Opening Gui again')
            self.open_settings_gui()

        # Data Monitors
        self.plotsReady = False
        self.init_plots()

        # Set timer for GUI-related tasks:
        self.timer = QTimer()
        self.timer.setInterval(10)  # every 50 ms it is called
        self.timer.timeout.connect(self.GUI_routines)
        self.timer.start()
        
        # Threading:
        self.worker_gatherer = Worker(self.gather_data)
        self.worker_communication = SignallingWorker(self.communication_routines)

        self.threadpool = QThreadPool()
        self.threadpool.start(self.worker_gatherer)
        self.threadpool.start(self.worker_communication)
        self.worker_communication.signals.result.connect(self.response_triggered)

    def gather_data(self):
        if not self.gatherer.connected:
            # If connection to Remote Data Access was not established yet
            return
        self.gatherer.fresh_init()
        while not self.quit:
            self.gatherer.main()
        self.gatherer.quit()

    def communication_routines(self):
        # if not self.internal_tcp.connected:
        #     return (False, False)
        self.communicate_state()
        respRequest = self.check_response()
        if respRequest:
            return (True, True)
        else:
            return (False, False)
            
    def GUI_routines(self):
        ''' Routines that are called using a timer ''' 
        if self.plotsReady:
            self.data_monitor.update(self.gatherer)

        if self.SubjectID != '' and self.plotsReady:
            
            self.checkUI()
            self.save()
            self.checkState()

    def check_response(self):
        ''' Receive response from participant through internal TCP connection with the 
            libet presentation
        '''
        if not self.internal_tcp.connected:
            # If connection is not established yet
            return False
        
        if self.internal_tcp.con.fileno() != -1:
            # If connection is running
            
            msg_libet = self.read_from_socket(self.internal_tcp)
            if msg_libet.decode(self.internal_tcp.encoding) == self.targetMarker or self.targetMarker in msg_libet.decode(self.internal_tcp.encoding):
                print('Response!')

                # self.responded = True
                
                self.checkState(recent_response=True)
                return True
            else:
                return False
        else:
            return

    def response_triggered(self, result):
        if result:
            # print('Signalling to .response_triggered(result) worked!')
            self.hist_monitor.button_press(self.gatherer)
            self.hist_monitor.plot_hist()

    def communicate_state(self, val=None):
        ''' This method communicates via the TCP Port that is connected with 
            the libet presentation.
        '''
        if not self.internal_tcp.connected:
            # If connection is not established yet
            return
        if self.internal_tcp.con.fileno() == -1:
            # If connection was closed at some point
            return

        if val is None:
            # Send Current state (allow or forbid) to the libet presentation
            allow_presentation = self.callbacks.allow_presentation
            msg = int(allow_presentation).to_bytes(1, byteorder='big')
            self.internal_tcp.con.send(msg)
            # print(f'sent {int(allow_presentation)} to libet PC')
        else:
            msg = int(val).to_bytes(1, byteorder='big')
            self.internal_tcp.con.send(msg)
            # print(f'sent {int(val)} to libet PC')  

    def checkUI(self):
        ''' Check the current state of all buttons and perform appropriate actions.'''
        # print('checking ui')
        
        new_state = np.clip(self.current_state + self.callbacks.stateChange, a_min = 0, a_max = 5)
        self.current_state = new_state

        if self.callbacks.stateChange != 0:
            print("allow_presentation = False now")
            self.callbacks.allow_presentation = False
        
        # Adjust GUI
        new_button_state = self.callbacks.permission_statement[self.callbacks.allow_presentation]
        current_button_state = self.buttonPresentationcontrol.text()
        if new_button_state != current_button_state:
            # change color
            if new_button_state == self.callbacks.permission_statement[0]:
                self.buttonPresentationcontrol.setStyleSheet("background-color: red")
            elif new_button_state == self.callbacks.permission_statement[1]:
                self.buttonPresentationcontrol.setStyleSheet("background-color: green")

        self.buttonPresentationcontrol.setText(self.callbacks.permission_statement[self.callbacks.allow_presentation])

        self.callbacks.stateChange = 0
        if self.callbacks.quit == True:
            self.current_state = 5

    def checkState(self, recent_response=False):
        ''' This method specifies the current state of the experiment.
            States are listed in get_statelist().
        '''
        # print('Checking state')
        if recent_response and (self.current_state == 1 or self.current_state == 3):
            self.check_if_interview()
            if self.go_interview:
                self.current_state += 1
                self.callbacks.presentToggle()
                
        if self.current_state == 0 and len(self.hist_monitor.scpAveragesList) >= self.hist_monitor.histcrit:
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
            # Send message to libet presentation that the experiment is over
            self.internal_tcp.con.setblocking(0)
            self.communicate_state(val=self.communicate_quit_code)

            response = self.read_from_socket(self.internal_tcp)
            
            
            while int.from_bytes(response, "big") != self.communicate_quit_code**2:
                print("waiting for libet to quit...")
                self.communicate_state(val=self.communicate_quit_code)
                response = self.read_from_socket(self.internal_tcp)
                time.sleep(0.1)
            print(f'Recieved response: {response}')
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

        if n_scps < self.hist_monitor.histcrit:
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

        if not self.go_interview and n_scps < self.histcrit:
            print("Too few trials to start interview.")
        if not self.go_interview and n_scps >= self.histcrit:
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
        self.current_state = 0

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

    def read_from_socket(self, socket):
        if socket.con.fileno() == -1:
            return

        ready = select.select([socket.con], [], [], socket.timeout)
        response = b''
        if ready[0]:
            response = socket.con.recv(socket.BufferSize)

        return response

    def save(self):
        ''' Save the current state of the experiment. 
        (not finished)
        '''
        print('saving')
        if not os.path.isdir('states/'):
            # If there is no folder to store states in -> create it
            os.mkdir('states/')

        State = {'scpAveragesList':self.hist_monitor.scpAveragesList, 
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




