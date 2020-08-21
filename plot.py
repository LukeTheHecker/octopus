import matplotlib.pyplot as plt
import numpy as np


class DataMonitor:
   
    def __init__(self, sr, package_size, window_len_s=10, figsize=(13,6), ylim=(-100, 100)):
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
        self.figsize = figsize
        self.ylim = ylim
        self.tolerance = 2.5
        # Data structures
        self.time = np.linspace(0, self.window_len_s, self.window_size)
        self.data_window = np.array([np.nan] * self.window_size)

        self.initialize_figure()

    def initialize_figure(self):
        '''
        '''
        plt.ion()
        fig = plt.figure(figsize=self.figsize)

        ax = fig.add_subplot(111)
        self.line, = ax.plot(self.time, self.data_window, linewidth=0.5)        
        plt.ylabel('Amplitude [microvolt]')
        # plt.title('Some title')
        plt.ylim(self.ylim)
        plt.xlim([self.time[0], self.time[-1]])
        plt.show()

    


    def update(self, data_package):
        ''' This method takes a data_package and plots it at the appropriate position in the data monitor plot
        Parameters:
        -----------
        data_package : list/numpy.ndarray, next data pack

        Return:
        -------
        '''
        
        self.data_window[self.cycle*self.package_size:(1 + self.cycle)*self.package_size] = data_package
        self.cycle += 1
        # If one window is full, start again on left side
        if self.cycle == self.n_cycles:
            print "data window = {}".format(self.data_window)
            plt.ylim([np.nanmin(self.data_window)*self.tolerance, np.nanmax(self.data_window)*self.tolerance])
            self.n_window += 1

            # print "Window is full, starting again \n"

            self.cycle = 0
            self.time =  np.linspace(self.n_window*self.window_len_s, (self.n_window + 1)*self.window_len_s, self.window_size)

            self.line.set_data(self.time, self.data_window)

            plt.xlim([np.min(self.time), np.max(self.time)])

        else:
            self.line.set_ydata(self.data_window)

        plt.pause(0.05)


# Create some signal
# from random import uniform

# sr = 500  # Hz
# total_dur_s = 10
# time = np.linspace(0, total_dur_s, total_dur_s * sr)
# n_oscillators = 100
# signal = np.zeros((len(time)))

# for osci in range(n_oscillators):
#     freq = uniform(0.01, 15)
#     multiplyer = 1/freq
#     signal = signal + np.sin(time * 2 * np.pi * freq) * multiplyer

# signal = (signal / np.max(np.abs(signal))) * 30


        

# sr = 500
# package_size = 20
# data_monitor = DataMonitor(sr, package_size)

# while True:
#     data_monitor.update(np.random.randn(package_size))
#     plt.pause(0.01)

# input('')