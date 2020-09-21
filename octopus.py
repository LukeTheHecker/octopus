import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor, Buttons, Textbox
from util import Scheduler
from communication import TCP
import select
import time
import numpy as np
import os
import json
import random
import asyncio

class Octopus:
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
        # Plot parameters
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

        self.startDialogue()         

        # Objects 
        self.callbacks = Callbacks()
        self.gatherer = Gather()
        self.internal_tcp = TCP()

        # Figure
        self.fig = plt.figure(num=42, figsize=figsize)
        # plt.ion()
        # plt.show(block=False)
        self.fig.tight_layout(pad=2)
        self.data_monitor = DataMonitor(self.gatherer.sr, self.gatherer.blockSize, fig=self.fig, update_frequency=self.update_frequency)
        self.hist_monitor = HistMonitor(self.gatherer.sr, fig=self.fig, 
            scp_trial_duration=self.scp_trial_duration, histcrit=self.histcrit, figsize=figsize)
        self.buttons = Buttons(self.fig, self.callbacks)
        self.textbox = Textbox(self.fig)
        # Conditions
        self.read_blinded_conditions()

        # Load state if needed:
        self.load()
    
    def startDialogue(self):
        self.SubjectID = input("Enter ID: ") 
    
    async def run(self):
        ''' Join tasks together in an asynchronous manner: Data gathering, 
        data monitoring, event handling.
        '''
        print("into the run")
        await asyncio.sleep(1)
        self.gatherer.fresh_init()

        tsk_gather = self.loop.create_task(self.gather_data())

        tsk_DMupdate = self.loop.create_task(self.update_data_monitor())

        tsk_checkState = self.loop.create_task(self.checkState())
        tsk_checkResponse = self.loop.create_task(self.check_response())
        tsk_communicateState = self.loop.create_task(self.communicate_state())
        tsk_checkUI = self.loop.create_task(self.checkUI())
        tsk_save = self.loop.create_task(self.save())
        # print('into the .wait:')
        await asyncio.wait([tsk_gather, tsk_DMupdate, tsk_checkState, tsk_checkResponse, 
            tsk_communicateState, tsk_checkUI, tsk_save])
        
        # print('out of the .wait:')
        # self.gatherer.quit()
        # self.loop.stop()
        # self.loop.close()

    def main(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.run())
        
        self.loop.close()

    async def gather_data(self, call_freq=10000000000):
        
        break_cond = (self.gatherer.con.fileno() != -1)

        while not self.quit:
            # print("starting data gathering")
            await self.gatherer.main(call_freq=call_freq)
            #print("done with data gathering")
            # break_cond = (self.gatherer.con.fileno() != -1)

    async def update_data_monitor(self, call_freq=20):
        while not self.quit:
            if call_freq is not None:
                await self.data_monitor.update(self.gatherer, call_freq)

    async def check_response(self, call_freq=10):
        ''' Receive response from participant through internal TCP connection with the 
            libet presentation
        '''
        # if n_new_blocks * self.block_duration < 1 / self.update_frequency:
        # self.gatherer.block_counter
        while not self.quit:
            if call_freq is not None:
                await asyncio.sleep(1 / call_freq)
                # print('checking response')

            if self.internal_tcp.con.fileno() != -1:
                msg_libet = self.read_from_socket(self.internal_tcp)
                if msg_libet.decode(self.internal_tcp.encoding) == self.targetMarker or self.targetMarker in msg_libet.decode(self.internal_tcp.encoding):
                    print('Response!')
                    # self.responded = True
                    print("1")
                    self.hist_monitor.button_press(self.gatherer)
                    print("2")
                    self.hist_monitor.plot_hist()
                    print("3")
                    self.checkState(recent_response=True)
                    print("4")
            else:
                return

    async def communicate_state(self, val=None, call_freq=5):
        ''' This method communicates via the TCP Port that is connected with 
            the libet presentation.
        '''
        while not self.quit:
            if call_freq is not None:
                await asyncio.sleep(1 / call_freq)

            if self.internal_tcp.con.fileno() == -1:
                return

            if val is None:
                # Send Current state (allow or forbid) to the libet presentation
                allow_presentation = self.callbacks.allow_presentation
                msg = int(allow_presentation).to_bytes(1, byteorder='big')
                self.internal_tcp.con.send(msg)
            else:
                msg = int(val).to_bytes(1, byteorder='big')
                self.internal_tcp.con.send(msg)
                break

            
            # print(f'sending state {msg}')

    async def checkUI(self, call_freq=10):
        ''' Check the current state of all buttons and perform appropriate actions.'''
        while True:
            if call_freq is not None:
                await asyncio.sleep(1 / call_freq)
            # print('checking ui')
            self.current_state = np.clip(self.current_state + self.callbacks.stateChange, a_min = 0, a_max = 5)
            if self.callbacks.stateChange != 0:
                print("allow_presentation = False now")
                self.callbacks.allow_presentation = False

            self.callbacks.stateChange = 0
            if self.callbacks.quit == True:
                self.current_state = 5
            # Adjust GUI
            self.buttons.buttonPresentationcontrol.label.set_text(self.callbacks.permission_statement[self.callbacks.allow_presentation])

    async def checkState(self, recent_response=False, call_freq=5):
        ''' This method specifies the current state of the experiment.
            States are listed in get_statelist().
        '''
        while not self.quit:
            if call_freq is not None:
                await asyncio.sleep(1 / call_freq)
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
                await self.communicate_state(val=self.communicate_quit_code)

                response = self.read_from_socket(self.internal_tcp)
                
        
                while int.from_bytes(response, "big") != self.communicate_quit_code**2:
                    await self.communicate_state(val=self.communicate_quit_code)
                    response = self.read_from_socket(self.internal_tcp)
                    asyncio.sleep(0.2)
                print(f'Recieved response: {response}')
                # Quit experiment
                print("Quitting...")
                self.quit = True
                self.gatherer.quit()
                self.internal_tcp.quit()
                self.save()
                self.loop.stop()
                self.loop.close()
                

                print(f'Quitted. self.internal_tcp.con.fileno()={self.internal_tcp.con.fileno()}')

            self.textbox.statusBox.set_text(f"State={self.current_state}\n{self.stateDescription[self.current_state]}")
        
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

    async def save(self, call_freq = 1):
        ''' Save the current state of the experiment. 
        (not finished)
        '''
        while True:
            if call_freq is not None:
                
                await asyncio.sleep(1 / call_freq)

            
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


if __name__ == '__main__':
    octopus = Octopus()
    octopus.main()