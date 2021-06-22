from octopus import model
import sys
from PyQt5.QtWidgets import *

if __name__ == '__main__':
    app = QApplication([sys.argv])
    window = model.Model()
    window.show()
    app.exec_()