import numpy as np
import time
import ctypes
from pyqtgraph.functions import interpolateArray

from scipy.stats import pearsonr
from scipy.optimize import minimize_scalar

from scipy.signal import periodogram
from scipy import argmax, trapz

import random
from mne.filter import filter_data

def insert(arr, piece):
    ''' Takes an array of values and a smaller array of values and 
    inserts the smaller array at the back without changing the 
    larger arrays size.
    Parameters:
    -----------
    arr : list/numpy.ndarray, an array of values
    piece : int/float/list/numpy.ndarray, a single value or array of values to insert at the end.
    '''
    assert type(arr) == list or type(arr) == np.ndarray, "arr must be of type list or numpy.ndarray but is of type {}".format(type(arr))
    
    if type(piece) == float or type(piece) == int:
        piece = np.array([piece])
    
    if type(piece) == list:
        piece = np.array(piece)
    
    if type(arr) == list:
        arr = np.array(arr)
    
    if len(arr.shape) == 1:
        arr = np.expand_dims(arr, axis=0)
    
    if len(piece.shape) == 1:
        piece = np.expand_dims(piece, axis=0)

    piecelen = piece.shape[1]
    new_arr = np.zeros(arr.shape)
    new_arr[:, 0:-piecelen] = arr[:, piecelen:]
    new_arr[:, -piecelen:] = piece

    return np.squeeze(new_arr)

def gui_retry_cancel(fun, text=('Connection could not be established.', 'Try again?')):
    MB_OK = 0x00000000
    result = ctypes.windll.user32.MessageBoxW(0, text[0], text[1], MB_OK)
    print(f'result={result}')
    if result == 1:
        print('Retrying...\n')
        fun()
    time.sleep(0.5)
    # fun()

def calc_error(EOG, Cz, d):
    error = abs(pearsonr(EOG, Cz - (EOG*d))[0])
    return error

def rms(x):
    return np.sqrt(np.mean(np.square(x)))

def demean(x):
    return x - np.mean(x)

def gradient_descent(fun, EOG, Cz, stepsize=0.1, max_iter=10000, maxStepDec=100):

    d = random.uniform(-0.5, 0.5)
    d_mem = [d]
    cont = True
    cnt = 0
    numberOfDecreasedStepsizes = 0

    while cont:
        current_error = fun(EOG, Cz, d)
        #print(f"current_error {current_error}")
        error_to_the_left = fun(EOG, Cz, d-stepsize)
        error_to_the_right = fun(EOG, Cz, d+stepsize)
        if error_to_the_left > error_to_the_right:
            d = d + stepsize
        else:
            d = d - stepsize     
        d_mem.append(d)


        if cnt > 3:
            if cnt >= max_iter: # or d_mem[-3] == d_mem [-1] or:
                numberOfDecreasedStepsizes += 1
                stepsize /= 2
                max_iter += 2
                # print(f'decreased stepsize to {stepsize}')
                if numberOfDecreasedStepsizes >= maxStepDec:
                    cont = False
        cnt += 1
        # print(f"cnt {cnt}: d changed to {d}") 
    print(f"Required {cnt} iterations.")
    return d

def estimate_d(VEOG, channel, maxiter=1000000):
    def fun(x, VEOG, channel):
        channel_corr = channel - VEOG*x
        return abs(pearsonr(channel_corr, VEOG)[0])
    opt = minimize_scalar(fun, args=(VEOG, channel), options=dict(maxiter=maxiter))
    return opt.x

def bandpower(x, fs, fmin, fmax):
    if any(np.isnan(x)):
        try:
            x = interp_nans(x)
        except:
            print("except!")
            return 0

    f, Pxx = periodogram(x, fs=fs, nfft=len(x)*10)
    ind_min = argmax(f > fmin) - 1
    ind_max = argmax(f > fmax) - 1
    return trapz(Pxx[ind_min: ind_max], f[ind_min: ind_max])


def freq_band_power(data, freqs, sr):
    ''' Simple function to calculate the frequency band power for a set of electrodes.
    Paramters:
    ----------
    data : list/numpy.ndarray, 1- or 2-D data.
    freqs : list/tuple, highpass cutoff and lowpass cutoff frequency in a list/tuple
    sr : int, sampling rate
    
    Return:
    -------
    meanScoreList : average frequency band power across selected channels.

    '''

    if type(data) == list:
        data = np.array(data)
    if len(data.shape) == 1:
        data = np.expand_dims(data, axis=0)

    scoreList = []
    # loop through all electrodes
    for elec in range(data.shape[0]):
        # Calculate score
        scoreList.append(bandpower(data[elec, :], sr, *freqs))
    meanScoreList = np.mean(scoreList)
    
    return meanScoreList
        
def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]

def interp_nans(y):
    nans, x= nan_helper(y)
    y[nans] = np.interp(x(nans), x(~nans), y[~nans])
    return y

class Scheduler:
    def __init__(self, list_of_functions, start, interval):
        self.list_of_functions = list_of_functions
        self.start = start
        self.interval = interval
        self.cnt = 1
        self.run_hist_intervals = []
        print("Initialized Scheduler")

    def run(self):
        end = time.time()
        current_time = round(end-self.start, 1)

        # Check if we maybe missed a round:
        target_time = round(self.interval * self.cnt, 1)
        # If difference between current time and the time when we want to start an interview is 
        # larger than two intervals we must have skipped something (because of timing issues).
        if current_time != 0 and (current_time - target_time) >= self.interval*2:
            self.cnt = int(round(current_time / self.interval))
            # print(f"missed at least a round, adjusting self.cnt to {self.cnt:.0f}!")

        # Execute all functions if interval is given
        if current_time  != 0 and current_time % target_time == 0:
            # print(f"Run functions {[t.__name__ for t in self.list_of_functions]} at {current_time}")
            self.run_hist_intervals.append(current_time)
            self.cnt += 1
            [fun() for fun in self.list_of_functions]
            

def pulse(x):
    ''' Returns a pulse of length x'''
    sr = 1
    freq = (1/x) / 2
    time = np.arange(x)

    signal = np.sin(2*np.pi*freq*time)
    return signal