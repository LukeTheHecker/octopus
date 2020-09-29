from PyQt5.QtCore import *

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
    result = pyqtSignal(object)

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

class SignallingWorker(QRunnable):
    '''
    Worker thread for Signalling
    
    This worker executes a function repeatedly and emits signals of this function based
    on its return value. The return of this function must be a list of two objects:
    First being boolean that says whether a signal should be emitted (True) or not (False).
    The second object in the list is the object to be emitted.
    
    Example:
    function returns -> (True, 11)
    This means that a signal 11 should be emitted.


    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(SignallingWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        while True:
            signal = self.fn(*self.args, **self.kwargs)
            if signal[0]:
                self.signals.result.emit(signal[1])

class EOGWorker(QRunnable):
    '''
    Worker thread for Signalling
    
    This worker executes a function repeatedly and emits signals of this function based
    on its return value. The return of this function must be a list of two objects:
    First being boolean that says whether a signal should be emitted (True) or not (False).
    The second object in the list is the object to be emitted.
    
    Example:
    function returns -> (True, 11)
    This means that a signal 11 should be emitted.


    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(EOGWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        print(f"self.args={self.args}")
        signal = self.fn(*self.args, **self.kwargs)

        self.signals.result.emit(signal)