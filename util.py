import numpy as np
import time
def insert(arr, piece):
    ''' Takes an array of values and a smaller array of values and 
    inserts the smaller array at the back without changing the 
    larger arrays size.
    Parameters:
    -----------
    arr : list/numpy.ndarray, an array of values
    piece : int/float/list/numpy.ndarray, a single value or array of values to insert at the end.
    '''
    assert type(arr) == list or type(arr) == np.ndarray, "arr must be of type list or numpy.ndarray but is of type {}".format(type(arr))
    # in case of piece being a single value: put in list
    if type(piece) == int or type(piece) == float:
        piece = [piece]

    piecelen = len(piece)
    new_arr = np.zeros((len(arr)))
    new_arr[0:-piecelen] = arr[piecelen:]
    new_arr[-piecelen:] = piece

    return new_arr

class Scheduler:
    def __init__(self, list_of_functions, start, interval):
        self.list_of_functions = list_of_functions
        self.start = start
        self.interval = interval
        self.cnt = 1
        print("Initialized Scheduler")

    def run(self):
        end = time.time()
        # Execute all functions if interval is given
        if round(end - self.start, 1)  != 0 and round(end - self.start, 1) % round(self.interval * self.cnt, 1) == 0:
            print(f"Run functions at {round(end-self.start, 1)}")
            self.cnt += 1
            [fun() for fun in self.list_of_functions]