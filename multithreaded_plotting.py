from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time
import pyqtgraph as pg
import sys
import traceback

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object, object)

class SignalWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, *args, **kwargs):
        super(SignalWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.abort = False
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.data = np.random.normal(size=(100,1000))
            ptr = 0
            while not self.abort:
                result = (self.data[ptr%10, :], ptr)
                self.signals.result.emit(*result)

                ptr += 1
                time.sleep(0.05)
                # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())    
            time.sleep(0.1)
            self.update()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        


        # Layout stuff
        # Menu
        
        # exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        # exitAct.setShortcut('Ctrl+Q')
        # exitAct.setStatusTip('Exit application')
        # exitAct.triggered.connect(qApp.quit)
        
        # menubar = self.menuBar()
        # fileMenu = menubar.addMenu('&File')
        # fileMenu.addAction(exitAct)


        # Main Widget
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        # Left Graph
        self.graphWidget1 = pg.PlotWidget()
        self.curve1 = self.graphWidget1.plot(pen="r")
        self.curve1.setData(np.random.randn(1000))
        # Title
        self.title = QLabel()
        self.title.setText("LOL")
        # Right Graph
        self.graphWidget2 = pg.PlotWidget()
        self.curve2 = self.graphWidget2.plot(pen="r")
        self.curve2.setData(np.random.randn(1000))
        # Add label
        self.label = QLabel()
        self.label.setText("Hello world")
        # Add button
        self.b = QPushButton("Stop signal")
        self.b.pressed.connect(self.quit)
        self.c = QPushButton ("Change Color")
        self.d = QPushButton ("Whatever")

        # Layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.graphWidget1, 1,0, 2, 4)
        self.layout.addWidget(self.title, 0,0, 1, 1)
        self.layout.addWidget(self.graphWidget2, 3,0, 2, 4)
        self.layout.addWidget(self.label, 1, 4, 2,4)
        self.layout.addWidget(self.b, 2, 5, 1, 1)
        self.layout.addWidget(self.c, 2, 6, 1, 1)
        self.layout.addWidget(self.d, 3, 5, 1, 1 )
        # self.layout.addWidget(self.titlewidget, 0, 0, 1, 1)
        # for i in range(4):
        #     self.layout.setColumnStretch(i, 2)

        self.mainWidget.setLayout(self.layout)
        
        
       # Threading
        self.threadpool = QThreadPool()

        worker_plot1 = SignalWorker()
        worker_plot1.signals.result.connect(self.plot1)
        self.threadpool.start(worker_plot1)

        worker_plot2 = SignalWorker()
        worker_plot2.signals.result.connect(self.plot2)
        self.threadpool.start(worker_plot2)


    def plot1(self, data, ptr):
        self.curve1.setData(data)
        self.title.setText(str(np.mean(data)))
        if ptr == 0:
            self.graphWidget1.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted

    def plot2(self, data, ptr):
        self.curve2.setData(data)
        # self.title.setText(str(np.mean(data)))
        if ptr == 0:
            self.graphWidget2.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted

    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def quit(self):
        self.abort = not self.abort

    
    
app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
# sys.exit(app.exec_())