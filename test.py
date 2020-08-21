import matplotlib.pyplot as plt
import numpy as np
from random import uniform

fig = plt.gcf()
fig.show()
fig.canvas.draw()

sr = 500  # Hz
total_dur_s = 15*60
time = np.linspace(0, total_dur_s, total_dur_s * sr)
n_oscillators = 100
signal = np.zeros((len(time)))

for osci in range(n_oscillators):
    freq = uniform(0.01, 15)
    multiplyer = 1/freq
    signal = signal + np.sin(time * 2 * np.pi * freq) * multiplyer

signal = (signal / np.max(np.abs(signal))) * 30

package_size = 50
window_len_s = 10
window_size = window_len_s*sr
n_cycles = int(round( window_size / package_size))


data_window = np.array([np.nan] * window_size)
# data_window[:] = np.nan



data_window[0:package_size] = signal[0:package_size]


plt.ion()
fig = plt.figure(figsize=(13,6))
ax = fig.add_subplot(111)
line1, = ax.plot(time[0:len(data_window)], data_window, linewidth=0.5)        
plt.ylabel('Y Label')
plt.title('Some title')
plt.ylim([-100, 100])
plt.xlim([0, time[len(data_window)]])
plt.show()

cycle = 0
cnt = 0
n_window = 0
tolerance = 2.5
response_happened = False

while True:
    data_window[cycle*package_size:(cycle+1)*package_size] = signal[cnt*package_size:(cnt+1)*package_size]

    cycle += 1
    cnt += 1
    
    # If one window is full, start again on left side
    if cycle == n_cycles:
        plt.ylim([np.min(data_window)*tolerance, np.max(data_window)*tolerance])
        n_window += 1

        # print "Window is full, starting again \n"

        cycle = 0
        new_time = time[n_window*len(data_window):(1+n_window)*len(data_window)]
        line1.set_data(new_time, data_window)
        plt.xlim([np.min(new_time), np.max(new_time)])
    else:
        line1.set_ydata(data_window)
        
    plt.pause(0.1)