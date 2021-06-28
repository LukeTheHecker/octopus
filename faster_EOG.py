import numpy as np
import matplotlib.pyplot as plt
import scipy
from scipy.optimize import minimize_scalar
from scipy.stats import pearsonr

t = np.arange(0, 10, 0.001)
sfreq = 1000
n = len(t)

def norm(x):
    return (x-x.mean()) / x.std()


center_span = range(int(n/2-1000), int(n/2+1000))
print(center_span)
pulse_freq = 1
damping_factor = 0.66737356


VEOG = norm(np.random.randn(n))/3
VEOG[center_span] += np.sin(2*np.pi*pulse_freq*t[center_span])

Cz = norm(np.random.randn(n) + VEOG*damping_factor)

# Minimize Scalar


def estimate_d(VEOG, channel):
    def fun(x, VEOG, channel):
        channel_corr = channel - VEOG*x
        return abs(pearsonr(channel_corr, VEOG)[0])
    opt = minimize_scalar(fun, args=(VEOG, Cz), options=dict(maxiter=1000000))
    return opt.x

Cz_corr = Cz - VEOG*opt.x
print(f'Scalar: {opt.x:.4f}')


plt.figure()
plt.subplot(311)
plt.plot(t, VEOG)
plt.title('VEOG')

plt.subplot(312)
plt.plot(t, Cz)
plt.title('Cz')

plt.subplot(313)
plt.plot(t, Cz_corr)
plt.title('Corrected')
plt.show()

# Cz = np.random.randn(n)
