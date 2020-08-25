import numpy as np

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