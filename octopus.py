from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from plot import MplCanvas
import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor, Buttons, Textbox
from communication import TCP
import select
import time
import numpy as np
import os
import json
import random
from myWorker import Worker

class Octopus(QMainWindow):
    def __init__(self, figsize=(13, 6), update_frequency=10, scp_trial_duration=2.5, 
        scp_baseline_duration=0.25, histcrit=5, targetMarker='response', 
        second_interview_delay=5):
        ''' Meta class that handles data collection, plotting and actions of the 
            SCP Libet Neurofeedback Experiment.
        Parameters:
        -----------
        figsize : list/tuple, size of the figure in which the data monitors etc. 
            will be plotted
        updatefrequency : int, frequenzy in Hz at which to update plots.
        scp_trial_duration : float, duration of an SCP in seconds. Baseline correction 
            depends on this
        scp_baseline_duration : float, duraion in seconds for baseline window 
            starting from -scp_trial_duration
        histcrit : int, minimum number of SCPs that are required before plotting a 
            histogram of their average values
        '''
        super(Octopus, self).__init__()

        # User input:
        self.startDialogue()
        # Objects 
        self.callbacks = Callbacks()
        self.gatherer = Gather()
        self.internal_tcp = TCP()
        self.gatherer.fresh_init()
        self.set_layout()
        

        # # Plot parameters
        self.scp_trial_duration=scp_trial_duration
        self.scp_baseline_duration=scp_baseline_duration
        self.histcrit=histcrit
        self.update_frequency = update_frequency
        
        # Action parameters
        self.targetMarker = targetMarker
        self.responded = False
        self.get_statelist()
        self.second_interview_delay = second_interview_delay
        self.communicate_quit_code = 2
        self.quit = False

              

        # Data Monitors
        self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, 
            curve=self.curve1, widget=self.graphWidget1, update_frequency=self.update_frequency,
            title=self.title)
        
        self.hist_monitor = HistMonitor(self.gatherer.sr, canvas=self.MplCanvas, 
            scp_trial_duration=self.scp_trial_duration, histcrit=self.histcrit)
        self.load()

        # Threading:
        self.worker_gatherer = Worker(self.gather_data)
        self.worker_datamonitor = Worker(self.update_data_monitor)
        self.worker_communication = Worker(self.communication_routines)
        self.worker_GUI_routines = Worker(self.GUI_routines)

        self.threadpool = QThreadPool()
        self.threadpool.start(self.worker_gatherer)
        self.threadpool.start(self.worker_datamonitor)
        self.threadpool.start(self.worker_communication)
        self.threadpool.start(self.worker_GUI_routines)

        print("done")
        # self.hist_monitor = HistMonitor(self.gatherer.sr, fig=self.fig, 
        #     scp_trial_duration=self.scp_trial_duration, histcrit=self.histcrit, figsize=figsize)

        # self.buttons = Buttons(self.fig, self.callbacks)
        # self.textbox = Textbox(self.fig)
        # # Conditions
        # self.read_blinded_conditions()

        # # Load state if needed:
        # 

        # List of functions to create threads for:
        # self.gatherer.fresh_init()

        # Gather Thread:
        # self.gather_data()

        ## Plot Thread:
        # self.update_data_monitor()

        # Routine Thread:
        # self.checkState()
        # self.check_response()
        # self.communicate_state()
        # self.checkUI()
        # self.save()
    
    def set_layout(self):
        # Layout stuff
        # self.setGeometry(300, 300, 250, 150)
        # Main Widget
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        # Left Graph
        self.graphWidget1 = pg.PlotWidget()
        self.curve1 = self.graphWidget1.plot(pen="r")
        # Title
        self.title = QLabel()
        self.title.setText("LOL")
        # Bottom Graph
        self.MplCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add label
        self.textBox = QLabel()
        self.textBox.setText("Hello world")
        # Add buttons
        self.buttonPresentationcontrol = QPushButton("Allow")
        self.buttonPresentationcontrol.pressed.connect(self.callbacks.presentToggle)
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

  

        self.mainWidget.setLayout(self.layout)

    def startDialogue(self):
        self.SubjectID = input("Enter ID: ") 
    
    def gather_data(self):
        while not self.quit:
            # print("go")
            # print("starting data gathering")
            self.gatherer.main()
            #print("done with data gathering")

    def update_data_monitor(self):
        while not self.quit:
            self.data_monitor.update(self.gatherer)
            time.sleep(0.1)

    def communication_routines(self):
        while not self.quit:
            self.communicate_state()
            self.check_response()
            self.checkState()

    def GUI_routines(self):
        while not self.quit:
            self.checkUI()
            self.save()

    def check_response(self):
        ''' Receive response from participant through internal TCP connection with the 
            libet presentation
        '''
        if self.internal_tcp.con.fileno() != -1:
            msg_libet = self.read_from_socket(self.internal_tcp)
            if msg_libet.decode(self.internal_tcp.encoding) == self.targetMarker or self.targetMarker in msg_libet.decode(self.internal_tcp.encoding):
                print('Response!')
                # self.responded = True
                self.hist_monitor.button_press(self.gatherer)
                self.hist_monitor.plot_hist()
                self.checkState(recent_response=True)
        else:
            return

    def communicate_state(self, val=None):
        ''' This method communicates via the TCP Port that is connected with 
            the libet presentation.
        '''
        if self.internal_tcp.con.fileno() == -1:
            return
        if val is None:
            # Send Current state (allow or forbid) to the libet presentation
            allow_presentation = self.callbacks.allow_presentation
            msg = int(allow_presentation).to_bytes(1, byteorder='big')
            self.internal_tcp.con.send(msg)
            print(f'sent {int(allow_presentation)} to libet PC')
        else:
            msg = int(val).to_bytes(1, byteorder='big')
            self.internal_tcp.con.send(msg)
            print(f'sent {int(val)} to libet PC')  

    def checkUI(self):
        ''' Check the current state of all buttons and perform appropriate actions.'''
        # print('checking ui')
        self.current_state = np.clip(self.current_state + self.callbacks.stateChange, a_min = 0, a_max = 5)
        if self.callbacks.stateChange != 0:
            print("allow_presentation = False now")
            self.callbacks.allow_presentation = False

        self.callbacks.stateChange = 0
        if self.callbacks.quit == True:
            self.current_state = 5
        # Adjust GUI
        self.buttonPresentationcontrol.setText(self.callbacks.permission_statement[self.callbacks.allow_presentation])

    def checkState(self, recent_response=False):
        ''' This method specifies the current state of the experiment.
            States are listed in get_statelist().
        '''
        # print('Checking state')
        if recent_response and (self.current_state == 1 or self.current_state == 3):
            self.check_if_interview()
            if self.go_interview:
                self.current_state += 1
                self.callbacks.presentToggle(None)
                
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
                self.communicate_state(val=self.communicate_quit_code)
                response = self.read_from_socket(self.internal_tcp)
                time.sleep(0.1)
            print(f'Recieved response: {response}')
            # Quit experiment
            print("Quitting...")
            self.quit = True
            self.gatherer.quit()
            self.internal_tcp.quit()
            self.close()
            print(f'Quitted. self.internal_tcp.con.fileno()={self.internal_tcp.con.fileno()}')

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
            # using the "second_interview_delay" variable.
            if n_scps < self.trials_until_first_interview + self.second_interview_delay:
                self.go_interview = False
            else:
                if condition == 'Positive':
                    self.go_interview = last_scp > avg_scp + sd_scp
                elif condition == 'Negative':
                    self.go_interview = last_scp < avg_scp - sd_scp

        if not self.go_interview:
            print("SCP not large enough or too few trials to start another interview.")

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
        if not os.path.isdir('states/'):
            # If there is no folder to store states in -> create it
            os.mkdir('states/')

        State = {'scpAveragesList':self.hist_monitor.scpAveragesList, 'current_state':int(self.current_state), 'SubjectID': self.SubjectID }

        json_file = json.dumps(State)

        filename = "states/" + self.SubjectID + '.json'
        with open(filename, 'w') as f:
            json.dump(json_file, f)
            
    def load(self):

        filename = "states/" + self.SubjectID + '.json'
        if not os.path.isfile(filename):
            print("No state found!")
            # self.save()

        else:
            answer = input(f"ID {self.SubjectID} already exists. Load data? [Y/N] ")
            if answer == "Y":
                with open(filename, 'r') as f:
                    json_file_read = json.load(f)
                
                State = json.loads(json_file_read)

                self.hist_monitor.scpAveragesList = State['scpAveragesList']
                self.current_state = State['current_state']
                self.SubjectID = State['SubjectID']
            elif answer == "N":
                self.save()

            else:
                self.load()



app = QApplication([])
window = Octopus()
window.show()
app.exec_()