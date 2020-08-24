import matplotlib.pyplot as plt
import numpy as np


class DataMonitor:
   
    def __init__(self, sr, package_size, fig=None, window_len_s=10, figsize=(13,6), ylim=(-100, 100)):
        print 'Yay Im initialized'
        # Basic Settings
        self.sr = sr
        self.window_len_s = window_len_s 
        self.package_size = package_size
        self.window_size = self.sr * self.window_len_s
        self.n_window = 0
        self.cycle = 0
        self.n_cycles = int(round( self.window_size / self.package_size))
        # Plot Settings
        self.fig = fig
        self.figsize = figsize
        self.ylim = ylim
        self.tolerance = 0.6
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


    def update(self, data_package, lagtime=None):
        ''' This method takes a data_package and plots it at the appropriate position in the data monitor plot
        Parameters:
        -----------
        data_package : list/numpy.ndarray, next data pack

        Return:
        -------
        '''
        assert len(data_package) == self.package_size, "Data package is of len {} but must be of len {}".format(len(data_package), self.package_size)
        
        self.data_window[self.cycle*self.package_size:(1 + self.cycle)*self.package_size] = data_package
        self.cycle += 1

        # If one window is full, start again on left side
        if self.cycle == self.n_cycles:
            self.n_window += 1

            # print "Window is full, starting again \n"

            self.cycle = 0
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


class HistMonitor:
    def __init__(self, sr, fig=None, trial_length_s=2.5, baseline_range_s=0.25, histcrit=10, figsize=(13,6)):
        self.sr = sr
        self.trial_length_s = trial_length_s
        self.baseline_range_s = baseline_range_s
        self.histcrit = histcrit
        self.package_size = None
        # Data
        self.dataMemory = np.array([np.nan] * int(round(self.trial_length_s*self.sr)))
        self.scpAveragesList = []
        # Figure
        self.fig = fig
        self.figsize = figsize
        self.initialize_figure()
        
    
    def initialize_figure(self):
        ''' Initialize the figure with empty data.'''

        if self.fig is None:
            self.fig = plt.figure(num=2, figsize=self.figsize)
            self.ax = self.fig.add_subplot(111)
        else:
            self.ax = self.fig.add_subplot(223)

        self.fig.canvas.draw()   # note that the first draw comes before setting data 

        self.title = self.ax.set_title("", loc='right', fontsize=14)

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
        tmpSCP -= np.mean(tmpSCP[0:int(self.baseline_range_s*self.sr)])
        self.scpAveragesList.append(np.mean(tmpSCP))

    def plot_hist(self):
        ''' Plot histogram of SCP averages if there are enough of them.'''
        if len(self.scpAveragesList) < self.histcrit:
            return
        # Calculate appropriate number of bins
        bins = int(4 + (len(self.scpAveragesList))/5)
        # Clear axis
        self.ax.cla()
        # Plot hist
        self.ax.hist(self.scpAveragesList, bins=bins)
        plt.draw()

        

# Create some signal
from random import uniform

sr = 500  # Hz
total_dur_s = 10
time = np.linspace(0, total_dur_s, total_dur_s * sr)
n_oscillators = 100
signal = np.zeros((len(time)))

for osci in range(n_oscillators):
    freq = uniform(0.01, 15)
    multiplyer = 1/freq
    signal = signal + np.sin(time * 2 * np.pi * freq) * multiplyer

signal = (signal / np.max(np.abs(signal))) * 30


        

# sr = 500
# package_size = 20
# data_monitor = DataMonitor(sr, package_size)

# while True:
#     data_monitor.update(np.random.randn(package_size))
#     plt.pause(0.01)

# input('')