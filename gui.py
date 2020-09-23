import ctypes

def gui_retry_cancel(fun):

    MB_RETRYCANCEL = 0x00000005


    result = ctypes.windll.user32.MessageBoxA(0, "Connection to brain vision rda could not be established", "How do you want to proceed?", MB_RETRYCANCEL)
    
    if result == 4:
        print('Retrying...\n')
        fun()
    elif result == 2:
        print('Cancelling...')

