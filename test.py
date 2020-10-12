import numpy as np
from scipy.stats import pearsonr
from scipy.signal import periodogram
from scipy import argmax, trapz
import scipy 

def bandpower(x, fs, fmin, fmax):
    f, Pxx = scipy.signal.periodogram(x, fs=fs, nfft=len(x)*10)
    print(f'f={f}, len(f)={len(f)}')
    print(f'Pxx={Pxx}')
    ind_min = scipy.argmax(f > fmin) - 1
    ind_max = scipy.argmax(f > fmax) - 1
    print(f'ind_min={ind_min}')
    print(f'ind_max={ind_max}')
    
    return scipy.trapz(Pxx[ind_min: ind_max], f[ind_min: ind_max])
    
a = np.random.randn(300)
print(bandpower(a, 1000, 8, 13))