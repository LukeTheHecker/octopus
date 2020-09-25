from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import time
import pyqtgraph as pg
import sys

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.abort = False


        # Layout stuff
        # self.setGeometry(300, 300, 250, 150)
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
       
        # self.b.move(35, 40)
        
        

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
        
        
       
 

        self.threadpool = QThreadPool()

        worker_plot1 = Worker(self.update)
        self.threadpool.start(worker_plot1)

        worker_plot2 = Worker(self.update2)
        self.threadpool.start(worker_plot2)



    def update_text(self):
        print('updating')
        val = np.random.randn(1)
        self.title.setText(str(val))


    def update(self):
        
        self.data = np.random.normal(size=(100,1000))
        ptr = 0
        while not self.abort:
            self.curve1.setData(self.data[ptr%10, :])
            if ptr == 0:
                self.graphWidget1.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
            ptr += 1
            
            self.title.setText(str(np.mean(self.data[ptr%10, :])))
            time.sleep(0.05)
            # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())    
        time.sleep(0.1)
        self.update()

    def update2(self):
        
        self.data = np.random.normal(size=(100,1000))
        ptr = 0
        while not self.abort:
            self.curve2.setData(self.data[ptr%10, :])
            if ptr == 0:
                self.graphWidget2.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
            ptr += 1
            time.sleep(0.05)

        time.sleep(0.1)
        self.update2()
            # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())   


    def quit(self):
        self.abort = not self.abort

    
    
app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
# sys.exit(app.exec_())