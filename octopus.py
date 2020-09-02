import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor, Buttons, Textbox
from util import Scheduler
from communication import InternalTCP
import select
import time
import numpy as np
import os
import json
import random

class Octopus:
    def __init__(self, figsize=(13, 6), update_frequency=10, scp_trial_duration=2.5, 
        scp_baseline_duration=0.25, histcrit=5, targetMarker='response', ):
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
        # Plot parameters
        self.scp_trial_duration=scp_trial_duration
        self.scp_baseline_duration=scp_baseline_duration
        self.histcrit=histcrit
        self.update_frequency = update_frequency
        
        # Action parameters
        self.targetMarker = targetMarker
        self.responded = False
        self.get_statelist()


        # Objects 
        self.callbacks = Callbacks()
        self.gatherer = Gather()
        self.internal_tcp = InternalTCP()

        # Figure
        self.fig = plt.figure(num=42, figsize=figsize)
        self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, fig=self.fig, update_frequency=self.update_frequency)
        self.hist_monitor = HistMonitor(self.gatherer.sr, fig=self.fig, 
            scp_trial_duration=self.scp_trial_duration, histcrit=self.histcrit, figsize=figsize)
        self.buttons = Buttons(self.fig, self.callbacks)
        self.textbox = Textbox(self.fig)
        # Conditions
        self.read_blinded_conditions()

    def check_response(self):
        ''' Receive response from participant through internal TCP connection with the 
            libet presentation
        '''
        # if n_new_blocks * self.block_duration < 1 / self.update_frequency:
        # self.gatherer.block_counter 

        ready = select.select([self.internal_tcp.con], [], [], self.internal_tcp.timeout)
        if ready[0]:
            msg_libet = self.internal_tcp.con.recv(self.internal_tcp.BufferSize)

            if msg_libet.decode(self.internal_tcp.encoding) == self.targetMarker or self.targetMarker in msg_libet.decode(self.internal_tcp.encoding):
                print('Response!')
                # self.responded = True
                self.hist_monitor.button_press()
                self.hist_monitor.plot_hist()
                self.checkState(recent_response=True)

    def communicate_state(self):
        ''' This method communicates via the internal TCP Port that is connected with 
            the libet presentation.
        '''
        # Communicate
        allow_presentation = self.callbacks.allow_presentation
        msg = int(allow_presentation).to_bytes(1, byteorder='big')
        self.internal_tcp.con.send(msg)

        # Adjust GUI
        self.buttons.buttonPresentationcontrol.label.set_text(self.callbacks.permission_statement[allow_presentation])
    
    def main(self):
        ''' Join tasks together in an asynchronous manner: Data gathering, 
        data monitoring, event handling.
        '''
        self.gatherer.fresh_init()
        
        # Schedule some functions
        
        scheduled_functions = [self.checkState, self.check_response, self.communicate_state]
        start = time.time()
        interval = 0.05  # seconds
        scheduler = Scheduler(scheduled_functions, start, interval)
        
        scheduled_functions = [self.checkUI]
        start = time.time()
        interval = 0.2  # seconds
        scheduler_slow = Scheduler(scheduled_functions, start, interval)



        while not self.callbacks.quit:

            self.gatherer.main()
            self.data_monitor.update(self.gatherer)
            self.hist_monitor.update_data(self.gatherer.data)  # check that data isnt stored twice
            scheduler.run()
            scheduler_slow.run()

        self.gatherer.quit()
        
    def checkUI(self):
        self.current_state =  np.clip(self.current_state + self.callbacks.stateChange, a_min = 0, a_max = 5)

        self.callbacks.stateChange = 0
        if self.callbacks.quit == True:
            self.current_state = 5

    def checkState(self, recent_response=False):
        ''' This method specifies the current state of the experiment.
            States are listed in get_statelist().
        '''
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
            # Quit experiment
            print("Quitting...")
            self.gatherer.quit()
            self.internal_tcp.quit()

        self.textbox.statusBox.set_text(f"State={self.current_state}\n{self.stateDescription[self.current_state]}")

    
    def check_if_interview(self):
        if not self.hist_monitor.scpAveragesList or len(self.hist_monitor.scpAveragesList) < self.hist_monitor.histcrit:
            print("too few SCPs in list, why are we in sucha  state????")
            self.go_interview = False
            return

        last_scp = self.hist_monitor.scpAveragesList[-1]
        avg_scp = np.median(self.hist_monitor.scpAveragesList)
        sd_scp = np.std(self.hist_monitor.scpAveragesList)

        self.go_interview = False

        # if we are right before first interview:
        if self.current_state == 1:
            key = self.cond_order[0]
            condition = self.conds[key]
            if condition == 'Positive':
                self.go_interview = last_scp > avg_scp + sd_scp
            elif condition == 'Negative':
                self.go_interview = last_scp < avg_scp - sd_scp

            
        elif self.current_state == 3:
            key = self.cond_order[1]
            condition = self.conds[key]
            if condition == 'Positive':
                self.go_interview = last_scp > avg_scp + sd_scp
            elif condition == 'Negative':
                self.go_interview = last_scp < avg_scp - sd_scp

        if not self.go_interview:
                    print("SCP not large enough")

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



octopus = Octopus()
octopus.main()