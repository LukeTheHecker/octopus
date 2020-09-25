# -*- coding: utf-8 -*-
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

# import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)
print(app)
win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples") # diese Überschrift ist nicht da
# win.resize(1000,600)
# win.setWindowTitle('pyqtgraph example: Plotting')

# Enable antialiasing for prettier plots
# pg.setConfigOptions(antialias=True)


p6 = win.addPlot(title="Updating plot")


def update():
    global p6
    curve = p6.plot(pen='r')
    data = np.random.normal(size=(100,1000))
    ptr = 0
    while True:
        curve.setData(data[ptr%10, :])
        if ptr == 0:
            p6.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
        ptr += 1
        time.sleep(0.05)


# The QTimer class provides a high-level programming interface for timers. To use it, create
# a QTimer, connect its timeout() signal to the appropriate slots, and call start(). 
# From then on, it will emit the timeout() signal at constant intervals.
threadpool = QThreadPool()

worker_plot1 = Worker(update)
threadpool.start(worker_plot1)


# timer = QtCore.QTimer()
# timer.timeout.connect(update) 
# timer.start(50) # interval at which the plot will be updated (update function will be called every 50 ms)


p7 = win.addPlot(title="Updating plot")

# data7 = np.random.normal(size=(100,1000))
# ptr7 = 0
def update2():
    global p7
    curve = p7.plot(pen='r')
    ptr = 0
    while True:
        data = np.random.normal(size=(100,1000))
        curve.setData(data[ptr%10, :])
        if ptr == 0:
            p7.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
        ptr += 1
        time.sleep(0.3)


worker_plot2 = Worker(update2)
threadpool.start(worker_plot2)

# The QTimer class provides a high-level programming interface for timers. To use it, create
# a QTimer, connect its timeout() signal to the appropriate slots, and call start(). 
# From then on, it will emit the timeout() signal at constant intervals.
# timer2 = QtCore.QTimer()
# timer2.timeout.connect(update2) 
# timer2.start(50) # interval at which the plot will be updated (update function will be called every 50 ms)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
