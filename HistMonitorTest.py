import matplotlib.pyplot as plt
import numpy as np
from random import uniform
import time
from plot import DataMonitor

sr = 500  # Hz
total_dur_s = 15*60
times = np.linspace(0, total_dur_s, total_dur_s * sr)
n_oscillators = 100
signal = np.zeros((len(times)))

for osci in range(n_oscillators):
    freq = uniform(0.01, 15)
    multiplyer = 1/freq
    signal = signal + np.sin(times * 2 * np.pi * freq) * multiplyer

signal = (signal / np.max(np.abs(signal))) * 30

package_size = 50
window_len_s = 10
window_size = window_len_s*sr
n_cycles = int(round( window_size / package_size))


data_window = np.array([np.nan] * window_size)
# data_window[:] = np.nan



data_window[0:package_size] = signal[0:package_size]


cycle = 0
cnt = 0
n_window = 0
tolerance = 2.5
response_happened = False
data_monitor = DataMonitor(sr, package_size)

dataMemoryDur_s = 2.5
dataMemory = np.array([np.nan] * int(round(dataMemoryDur_s*sr)))
button_press = False
scpAveragesList = []
baseline_length_s = 0.1

fig = plt.figure(42)
ax = fig.add_subplot(111)
while True:
    data = signal[cnt*package_size:(cnt+1)*package_size]
    # Add new data in the end and delete data in the beginning:
    tmpDataMemory = np.zeros((len(dataMemory)))
    tmpDataMemory[0:-package_size] = dataMemory[package_size:]
    tmpDataMemory[-package_size:] = data
    dataMemory = tmpDataMemory

    lowprob = np.random.rand(1)
    if lowprob < 0.30 and not np.isnan(dataMemory).any():
        button_press = True
        tmpSCP = dataMemory.copy()
        # Correct baseline
        tmpSCP -= np.mean(tmpSCP[0:int(baseline_length_s*sr)])
        scpAveragesList.append(np.mean(tmpSCP))
        print "scpAveragesList={}".format(scpAveragesList)
        

    else:
        button_press = False

    if len(scpAveragesList) == 50:
        ax.hist(scpAveragesList, bins=20)

    data_monitor.update(data)

    # Handle Button press
    if button_press:
        print "yes"

    cycle += 1
    cnt += 1
    time.sleep(0.1)
