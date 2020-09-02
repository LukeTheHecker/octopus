import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
from numpy.core.shape_base import block
from util import *
import asyncio
import seaborn as sns
# from callbacks import Callbacks

class DataMonitor:
   
    def __init__(self, sr, block_size, fig=None, window_len_s=10, figsize=(13,6), ylim=(-100, 100), update_frequency=10):
        print('DataMonitor initialized')
        # Basic Settings
        self.sr = sr
        self.window_len_s = window_len_s 
        self.window_size = self.sr * self.window_len_s
        self.n_window = 0
        self.block_size = block_size
        self.block_duration = self.block_size / float(self.sr)
        assert round(self.window_size / self.block_size) == self.window_size / self.block_size, 'window size not divisible by block size, please adjust window size'
        self.n_blocks = int(self.window_size / self.block_size)
        self.blockMemory = [-1] * self.n_blocks
        self.blockCount = 0
        # Plot Settings
        self.fig = fig
        self.figsize = figsize
        self.ylim = ylim
        self.tolerance = 0.6
        self.update_frequency = update_frequency
        # Data structures
        self.time = np.linspace(0, self.window_len_s, self.window_size)
        self.data_window = np.array([np.nan] * self.window_size)
        self.initialize_figure()

    def initialize_figure(self):
        '''
        '''
        if self.fig is None:
            self.fig = plt.figure(num=1, figsize=self.figsize)
            self.ax = self.fig.add_subplot(111)
        else:
            self.ax = self.fig.add_subplot(221)

        self.fig.canvas.draw()   # note that the first draw comes before setting data 

        self.title = self.ax.set_title("", loc='right', fontsize=14)

        self.axbackground = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.line, = self.ax.plot(self.time, self.data_window, linewidth=0.5)        
        plt.ylabel('Amplitude [microvolt]')
        # plt.title('Some title')
        plt.ylim(self.ylim)
        plt.xlim([self.time[0], self.time[-1]])
        plt.show(block=False)


    def update(self, gatherer):
        ''' This method takes a data_package and plots it at the appropriate position in the data monitor plot
        Parameters:
        -----------
        data_package : list/numpy.ndarray, next data pack

        Return:
        -------
        '''
        dataMemory = gatherer.dataMemory
        IncomingBlockMemory = gatherer.blockMemory
        lagtime = gatherer.lag_s

        if np.max(IncomingBlockMemory) <= np.max(self.blockMemory):
            # all blocks have been plotted
            return

        n_new_blocks = int(np.max(IncomingBlockMemory) - np.max(self.blockMemory))
        
        if n_new_blocks * self.block_duration < 1 / self.update_frequency:
            return

        new_blocks = np.arange(np.max(self.blockMemory) + 1, np.max(self.blockMemory) + 1 + n_new_blocks).astype(int)
        # print(f'new_blocks={new_blocks}')
        # Block count of the first block that is new
        first_new_block = np.max(self.blockMemory) + 1
        # Block position that shall be replaced first
        block_of_first_replacement = first_new_block % self.n_blocks
        # Index of said block position
        idx_of_first_replacement = int(block_of_first_replacement * self.block_size)
        # print(f'idx_of_first_replacement={idx_of_first_replacement}')
        # Extract new portion of data
        data_pack = dataMemory[-n_new_blocks*self.block_size:]

        # If new portion of data goes beyong the window boundary:
        if idx_of_first_replacement + len(data_pack) > self.window_size:
            new_win = True
            self.data_window[idx_of_first_replacement:] = data_pack[0:len(self.data_window[idx_of_first_replacement:])]

            if len(self.data_window[idx_of_first_replacement:]) != len(data_pack):
                remainder_length = int(len(data_pack) - len(data_pack[0:len(self.data_window[idx_of_first_replacement:])]))
                # print(remainder_length)
                self.data_window[0:remainder_length] = data_pack[len(self.data_window[idx_of_first_replacement:]):]
        else:
            self.data_window[idx_of_first_replacement:idx_of_first_replacement+len(data_pack)] = data_pack
            # print(f'new_blocks: {new_blocks}')
            # print(f'np.mod(new_blocks, self.window_size)={np.mod(new_blocks, self.window_size / self.n_blocks)}')
            if any(np.mod(new_blocks, self.window_size / self.block_size) == 0):
                new_win = True
            else:
                new_win = False
        # print(f'new_win={new_win}')
        # If one window is full, start again on left side
        if new_win and self.blockCount != 0:
            self.n_window += 1

            # print("Window is full, starting again \n")

            self.time = np.linspace(self.n_window*self.window_len_s, (self.n_window + 1)*self.window_len_s, self.window_size)

            self.line.set_data(self.time, self.data_window)

            self.ax.set_xlim([np.min(self.time), np.max(self.time)])
            # New y limits
            data_range = np.nanmax(self.data_window) - np.nanmin(self.data_window)
            new_limits = (np.nanmin(self.data_window) - data_range*self.tolerance, np.nanmax(self.data_window) + data_range*self.tolerance)
            self.ax.set_ylim(new_limits)

            self.fig.canvas.draw()
            plt.show(block=False)
        else:
            self.line.set_ydata(self.data_window)
        
        if lagtime is not None:
            self.title.set_text("Lag = {:.2f} s".format(lagtime))
            plt.draw()
        

        self.fig.canvas.restore_region(self.axbackground)
        self.ax.draw_artist(self.line)
        self.fig.canvas.blit(self.ax.bbox)
        self.fig.canvas.flush_events()

        
        self.blockMemory = IncomingBlockMemory
        self.blockCount += n_new_blocks


class HistMonitor:
    def __init__(self, sr, fig=None, scp_trial_duration=2.5, scp_baseline_duration=0.25, 
            histcrit=5, figsize=(13,6)):
        
        self.sr = sr
        self.scp_trial_duration = scp_trial_duration
        self.scp_baseline_duration = scp_baseline_duration
        self.histcrit = histcrit
        self.package_size = None
        # Data
        self.dataMemory = np.array([np.nan] * int(round(self.scp_trial_duration*self.sr)))
        self.scpAveragesList = []
        self.n_responses = len(self.scpAveragesList)
        # Figure
        self.fig = fig
        self.figsize = figsize
        self.initialize_figure()
        # Action Paramters
        self.current_state = None
        print("HistMonitor initialized")
        
    
    def initialize_figure(self):
        ''' Initialize the figure with empty data.'''

        if self.fig is None:
            self.fig = plt.figure(num=2, figsize=self.figsize)
            self.ax = self.fig.add_subplot(111)
        else:
            self.ax = self.fig.add_subplot(223)

        self.fig.canvas.draw()   # note that the first draw comes before setting data 

        self.title = f'Histogram of {self.n_responses} responses'
        self.ax.set_title(self.title, fontsize=14)

        self.axbackground = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.hist = self.ax.hist([-1, 0, 1])   
        self.ax.cla()

        plt.ylabel('Amplitude [microvolt]')
        
        plt.show(block=False)
        
    def update_data(self, data_package):
        ''' Collect new data and add it to the data memory.
        Parameters:
        -----------
        data_package : numpy.ndarray/list, new data retrieved from rda.
        '''
        if self.package_size is None:
            self.package_size = len(data_package)

        assert self.package_size == len(data_package), "package_size is supposed to be {} but data was of size {}".format(self.package_size, len(data_package))

        tmpDataMemory = np.zeros((len(self.dataMemory)))
        tmpDataMemory[0:-self.package_size] = self.dataMemory[self.package_size:]
        tmpDataMemory[-self.package_size:] = data_package
        self.dataMemory = tmpDataMemory

    
    def button_press(self):
        ''' If a button was pressed append the average baseline corrected SCP to a list.
        '''
        tmpSCP = self.dataMemory.copy()
        # Correct baseline
        tmpSCP -= np.mean(tmpSCP[0:int(self.scp_baseline_duration*self.sr)])
        self.scpAveragesList.append(np.mean(tmpSCP))
        
        self.n_responses = len(self.scpAveragesList)
        self.title = f'Histogram of {self.n_responses} responses'
        self.ax.set_title(self.title, fontsize=14)

    def plot_hist(self):
        ''' Plot histogram of SCP averages if there are enough of them.'''
        if len(self.scpAveragesList) < self.histcrit:
            return
        # Calculate appropriate number of bins
        bins = int(4 + (len(self.scpAveragesList))/5)
        # Clear axis
        self.ax.cla()
        # Plot hist
        sns.distplot(self.scpAveragesList, ax=self.ax)
        # self.ax.hist(self.scpAveragesList, bins=bins)

        # Update title
        self.n_responses = len(self.scpAveragesList)
        self.title = f'Histogram of {self.n_responses} responses'
        self.ax.set_title(self.title, fontsize=14)

        plt.draw()

class Buttons:
    def __init__(self, fig, callbacks):
        self.fig = fig
        self.callbacks = callbacks

        ax = self.fig.add_axes([0.70, 0.4, 0.1, 0.075])
        self.buttonPresentationcontrol = Button(ax, '')
        self.buttonPresentationcontrol.on_clicked(self.callbacks.presentToggle)

        ax = self.fig.add_axes([0.85, 0.05, 0.1, 0.075])
        self.buttonQuit = Button(ax, 'Quit')
        self.buttonQuit.on_clicked(self.callbacks.quitexperiment)

        ax = self.fig.add_axes([0.75, 0.30, 0.05, 0.075])
        self.buttonforward = Button(ax, '->')
        self.buttonforward.on_clicked(self.callbacks.stateforward)

        ax = self.fig.add_axes([0.7, 0.30, 0.05, 0.075])
        self.buttonbackwards = Button(ax, '<-')
        self.buttonbackwards.on_clicked(self.callbacks.statebackwards)






class Textbox:
    def __init__(self, fig):
        self.fig = fig
        ax = self.fig.add_subplot(222)

        ax.xaxis.set_visible(False) 
        ax.yaxis.set_visible(False)

        # ax = self.fig.add_axes([0.1, 0.05, 0.2, 0.1])
        self.statusBox = ax.text(0.05, 0.75, "Status", fontsize=12, wrap=True, ha='left')