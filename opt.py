import numpy as np
import matplotlib.pyplot as plt
from util import gradient_descent, calc_error, rms, demean
from scipy.signal import detrend
## Create Signal with damp factor "d"
dur = 10  # 
sr = 250  # Hz
time = np.arange(0, 10, 1/sr)

blink_frequency = 2
EOG = np.sin(2*np.pi*blink_frequency*time) * 1e3
drift = np.sin(2*np.pi*0.01*time) * 1e3


d_real = 0.005

Cz_clean = np.cumsum(np.random.randn(int(round(sr*dur))))
Cz = Cz_clean + (EOG * d_real)
# Add drift due to sweat or other causes
EOG += drift

# Prepare Signal
EOG = detrend(EOG)
## Estimate d
scale = rms(Cz) / rms(EOG)
d_est = gradient_descent(calc_error, EOG*scale, Cz)
print(f'Scaled:\n')
print(f'd_est={d_est}')
print(f'scale={scale}')
print(f'd_est*scale={d_est*scale}')
print(f'd_real={d_real}')
d_est *= scale

error = abs(d_est-d_real) / d_real
## Plot result
plt.figure()

plt.subplot(411)
plt.plot(time, EOG)
plt.title(f'EOG')

plt.subplot(412)
plt.plot(time, Cz)
plt.title(f'Cz with artifacts')

plt.subplot(413)
plt.plot(time, Cz - (EOG * d_est))
plt.title(f'Cz cleaned. d={d_est:.4f}, error={100*error:.2f}%')

plt.subplot(414)
plt.plot(time, Cz_clean )
plt.title(f'Clean Cz.')

plt.show()

