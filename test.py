#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mne.filter import filter_data, create_filter, resample
import numpy as np
import time
import matplotlib.pyplot as plt
dur = 2.5
sr = 250



signal = np.random.randn(int(dur*sr))
start = time.time()
plt.figure()
plt.plot(signal, 'k')

# signal = resample(signal, down=2.5)
# sr = 100

signal = filter_data(signal, sr, 0, 1, verbose=0)
plt.plot(signal, 'r')
end = time.time()
print(f'time elapsed: {end-start:.2f}')
# print(signal)

plt.show()