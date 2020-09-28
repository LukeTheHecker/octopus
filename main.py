from octopus import Octopus
import sys
from PyQt5.QtWidgets import *

if __name__ == '__main__':
    app = QApplication([sys.argv])
    window = Octopus()
    window.show()
    app.exec_()