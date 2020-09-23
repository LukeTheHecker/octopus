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
curve = p6.plot(pen='r')
data = np.random.normal(size=(100,1000))
ptr = 0
def update():
    global curve, data, ptr, p6
    curve.setData(data[ptr%10])
    if ptr == 0:
        p6.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1


# The QTimer class provides a high-level programming interface for timers. To use it, create
# a QTimer, connect its timeout() signal to the appropriate slots, and call start(). 
# From then on, it will emit the timeout() signal at constant intervals.
timer = QtCore.QTimer()
timer.timeout.connect(update) 
timer.start(50) # interval at which the plot will be updated (update function will be called every 50 ms)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
