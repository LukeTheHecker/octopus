from util import pulse
import matplotlib.pyplot as plt
import numpy as np
plt.figure()
plt.plot(np.arange(100), pulse(100))
plt.show()
