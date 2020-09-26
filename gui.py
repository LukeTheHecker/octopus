import ctypes
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys

def gui_retry_cancel(fun):

    MB_RETRYCANCEL = 0x00000005


    result = ctypes.windll.user32.MessageBoxA(0, "Connection to brain vision rda could not be established", "How do you want to proceed?", MB_RETRYCANCEL)
    
    if result == 4:
        print('Retrying...\n')
        fun()
    elif result == 2:
        print('Cancelling...')


class SettingsGui(QMainWindow):
    def __init__(self, parent=None):
        super(SettingsGui, self).__init__(parent)

        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(280,40)

        # Define attributes
        self.id = self.textbox.text()
        