from gather import Gather
from plot import DataMonitor, HistMonitor, Buttons
from matplotlib import pyplot as plt

from callbacks import Callbacks

# from tcp import internalTCP



hist_monitor = HistMonitor()
buttons = Buttons(fig, callbacks)
# internal_TCP = internalTCP()

while True:
    gatherer.main()
    gatherer.data
    gatherer.dataMemory
    data_monitor.update(gatherer.dataMemory, gatherer.blockMemory)

    hist_monitor.update(gatherer.data)

    # internal_TCP.recv()
    # if internal_TCP.hasresponse():
    #     hist_monitor.button_press()
    #     hist_monitor.plot_hist()
