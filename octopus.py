import matplotlib.pyplot as plt
from callbacks import Callbacks
from gather import Gather
from plot import DataMonitor, HistMonitor, Buttons
from util import Scheduler
from communication import InternalTCP
import select
import time


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
    
    def check_response(self):
        '''Receive response from participant through internal TCP connection with the 
            libet presentation'''
        # if n_new_blocks * self.block_duration < 1 / self.update_frequency:
        # self.gatherer.block_counter 

        ready = select.select([self.internal_tcp.con], [], [], self.internal_tcp.timeout)
        if ready[0]:
            msg_libet = self.internal_tcp.con.recv(self.internal_tcp.BufferSize)

            if msg_libet.decode(self.internal_tcp.encoding) == self.targetMarker or self.targetMarker in msg_libet.decode(self.encoding):
                print('Response!')
                # self.responded = True
                self.hist_monitor.button_press()
                self.hist_monitor.plot_hist()

    def communicate_state(self):
        state = self.callbacks.state
        msg = int(state).to_bytes(1, byteorder='big')

        self.internal_tcp.con.send(msg)

        # print(f'sent message {int.from_bytes(msg, "big")}')
    
    def main(self):
        ''' Join tasks together in an asynchronous manner: Data gathering, 
        data monitoring, event handling.
        '''
        self.gatherer.fresh_init()
        
        # Schedule some functions
        
        scheduled_functions = [self.check_response, self.communicate_state]
        start = time.time()
        interval = 0.1  # seconds
        scheduler = Scheduler(scheduled_functions, start, interval)
        
        while not self.callbacks.quit:

            self.gatherer.main()
            self.data_monitor.update(self.gatherer)
            self.hist_monitor.update_data(self.gatherer.data)  # check that data isnt stored twice
            scheduler.run()
            

        self.gatherer.quit()

octopus = Octopus()
octopus.main()