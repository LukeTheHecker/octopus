import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
from numpy.core.shape_base import block
from util import *
import asyncio
import seaborn as sns

import matplotlib
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

# from callbacks import Callbacks

class DataMonitor:
   
    def __init__(self, sr, block_size, curve, widget, window_len_s=10, figsize=(13,6), ylim=(-100, 100), 
        title=None, channelOfInterestIdx=None, blinder=1):
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
        self.curve = curve
        self.widget = widget
        self.title = title
        self.ylim = ylim
        self.tolerance = 0.6
        self.channelOfInterestIdx = channelOfInterestIdx
        # Blinding the direction of the effect:
        self.blinder = blinder
        # Data structures
        self.time = np.linspace(0, self.window_len_s, self.window_size)
        self.data_window = np.array([np.nan] * self.window_size)
        self.initialize_figure()

    def initialize_figure(self):
        '''
        '''
        # Add title
        # Add axis labels
        # self.curve.setData(self.time, self.data_window*self.blinder, connect="finite")
        self.widget.setXRange(np.min(self.time), np.max(self.time), padding=0)
        self.widget.setYRange(self.ylim[0], self.ylim[1], padding=0)

    def update(self, gatherer):
        ''' This method takes a data_package and plots it at the appropriate position in the data monitor plot
        Parameters:
        -----------
        data_package : list/numpy.ndarray, next data pack

        Return:
        -------
        '''
        if not gatherer.connected:
            return

        dataMemory = gatherer.dataMemory[self.channelOfInterestIdx, :]
        IncomingBlockMemory = gatherer.blockMemory
        lagtime = gatherer.lag_s

        

        n_new_blocks = int(np.max(IncomingBlockMemory) - np.max(self.blockMemory))
        

        if np.max(IncomingBlockMemory) == np.max(self.blockMemory):
            # all blocks have been plotted
            # print('all blocks have been plotted')
            return

        new_blocks = np.arange(np.max(self.blockMemory) + 1, np.max(self.blockMemory) + 1 + n_new_blocks).astype(int)
        # Block count of the first block that is new
        first_new_block = np.max(self.blockMemory) + 1
        # Block position that shall be replaced first
        block_of_first_replacement = first_new_block % self.n_blocks
        # Index of said block position
        idx_of_first_replacement = int(block_of_first_replacement * self.block_size)
        # Extract new portion of data
        data_pack = np.array(dataMemory[-n_new_blocks*self.block_size:])
        # If new portion of data goes beyong the window boundary:
        if idx_of_first_replacement + len(data_pack) > self.window_size:
            new_win = True
            self.data_window[idx_of_first_replacement:] = data_pack[0:len(self.data_window[idx_of_first_replacement:])]

            if len(self.data_window[idx_of_first_replacement:]) != len(data_pack):
                remainder_length = int(len(data_pack) - len(data_pack[0:len(self.data_window[idx_of_first_replacement:])]))
                self.data_window[0:remainder_length] = data_pack[len(self.data_window[idx_of_first_replacement:]):]
        else:
            self.data_window[idx_of_first_replacement:idx_of_first_replacement+len(data_pack)] = data_pack
            if any(np.mod(new_blocks, self.window_size / self.block_size) == 0):
                new_win = True
            else:
                new_win = False

        # If one window is full, start again on left side
        if new_win: # and self.blockCount != 0:
            # print("starting new window")
            self.time = np.linspace(self.n_window*self.window_len_s, (self.n_window + 1)*self.window_len_s, self.window_size)
            # New x and y limits
            new_limits = self.decide_ylimits()

            # Handle discontinuities in the data
            con = np.isfinite(self.data_window)
            self.data_window[~con] = 0
            # Plot
            self.curve.setData(self.time, self.data_window*self.blinder, connect=np.logical_and(con, np.roll(con, -1)))
            self.widget.setXRange(np.min(self.time), np.max(self.time), padding=0)
            self.widget.setYRange(*new_limits, padding=0)

            self.n_window += 1
        else:
            con = np.isfinite(self.data_window)
            self.data_window[~con] = 0
            # Plot
            self.curve.setData(self.time, self.data_window*self.blinder, connect=np.logical_and(con, np.roll(con, -1)))

        
        if lagtime is not None:
            self.title.setText(f'lag={lagtime:.1f}s')
            
        self.blockMemory = IncomingBlockMemory
        self.blockCount += n_new_blocks

    def decide_ylimits(self):
        ''' Collect the ylimits of each new window and calculate the optimal window size using 5th percentile of lowest
        values and 95th percentile of highest values.'''
        
        data_range = np.nanmax(self.data_window*self.blinder) - np.nanmin(self.data_window*self.blinder)
        lo, hi = (np.nanmin(self.data_window*self.blinder) - data_range*self.tolerance, np.nanmax(self.data_window*self.blinder) + data_range*self.tolerance)

        if not hasattr(self, "minlims"):
            self.minlims = [lo]
            self.maxlims = [hi]
            return (lo, hi)

        self.minlims.append(lo)
        self.maxlims.append(hi)
        new_limits = (np.percentile(self.minlims, 5), np.percentile(self.maxlims, 95))
        return new_limits




    @staticmethod
    def firstNonNan(listfloats):
        for i, item in enumerate(listfloats):
            if np.isnan(item) == False:
                return i

class HistMonitor:
    def __init__(self, sr, canvas, SCPTrialDuration=2.5, scpBaselineDuration=0.25, 
            histCrit=5, figsize=(13,6), channelOfInterestIdx=None, blinder=1):
        self.canvas = canvas
        self.sr = sr
        self.SCPTrialDuration = SCPTrialDuration
        self.scpBaselineDuration = scpBaselineDuration
        self.histCrit = histCrit
        self.package_size = None
        # Data
        self.dataMemory = np.array([np.nan] * int(round(self.SCPTrialDuration*self.sr)))
        self.scpAveragesList = np.array([])
        self.n_responses = len(self.scpAveragesList)
        self.channelOfInterestIdx = channelOfInterestIdx
        # Figure
        self.initialize_figure()
        # Blinding the direction of the effect:
        self.blinder = blinder
        # Action Paramters
        self.current_state = None
        print("HistMonitor initialized")
        
    
    def initialize_figure(self):
        ''' Initialize the figure with empty data.'''
        
        self.title = f'Histogram of {self.n_responses} responses'
        self.canvas.ax.set_title(self.title, fontsize=14)

        self.hist = self.canvas.ax.hist([-1, 0, 1])   
        self.canvas.ax.cla()
        self.canvas.ax.set_ylabel('Amplitude [microvolt]')
                
        
    def button_press(self, gatherer):
        ''' If a button was pressed append the average baseline corrected SCP to a list.
        '''
        # Get data from gatherer:
        back_idx = int(self.SCPTrialDuration * self.sr)
        tmpSCP = gatherer.dataMemory[self.channelOfInterestIdx, -back_idx:]
        # Correct Baseline:
        tmpSCP -= np.mean(tmpSCP[0:int(self.scpBaselineDuration*self.sr)])
        # Save average
        self.scpAveragesList = np.append(self.scpAveragesList, np.mean(tmpSCP))
        
        self.n_responses = len(self.scpAveragesList)
        self.title = f'Histogram of {self.n_responses} responses'
        self.canvas.ax.set_title(self.title, fontsize=14)

    def plot_hist(self):
        ''' Plot histogram of SCP averages if there are enough of them.'''
        
        # Clear axis
        self.canvas.ax.clear()
        if len(self.scpAveragesList) < self.histCrit and len(self.scpAveragesList) > 1:
            sns.distplot(self.scpAveragesList*self.blinder, ax=self.canvas.ax, rug=True, kde=False,
                hist=True)
            
        elif len(self.scpAveragesList) >= self.histCrit:
            sns.distplot(self.scpAveragesList*self.blinder, ax=self.canvas.ax, rug=True, kde=True,
                hist=True)
            # Get the maximum value of the kde distribution
            maxval = np.max(sns.distplot(self.scpAveragesList*self.blinder, ax=self.canvas.ax, rug=True, kde=True, 
                hist=True).get_lines()[0].get_data()[1])

            self.canvas.ax.plot([self.scpAveragesList[-1]*self.blinder, self.scpAveragesList[-1]*self.blinder], [0, maxval], 'r')
        else:
            return 
        # Update title
        self.n_responses = len(self.scpAveragesList)
        self.title = f'Histogram of {self.n_responses} responses'
        self.canvas.ax.set_title(self.title, fontsize=14)
        self.canvas.draw()


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

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=600):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)