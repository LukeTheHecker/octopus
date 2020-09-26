# file ui_main.py
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(584, 897)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 584, 21))
        self.menubar.setObjectName("menubar")
        self.menuPreferences = QtWidgets.QMenu(self.menubar)
        self.menuPreferences.setObjectName("menuPreferences")
        MainWindow.setMenuBar(self.menubar)
        self.setPreferencesAction = QtWidgets.QAction(MainWindow)
        self.setPreferencesAction.setObjectName("setPreferencesAction")
        self.menuPreferences.addAction(self.setPreferencesAction)
        self.menubar.addAction(self.menuPreferences.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuPreferences.setTitle(_translate("MainWindow", "Settings"))
        self.setPreferencesAction.setText(_translate("MainWindow", "Preferences"))

# file ui_dialog.py
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(508, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(150, 250, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.sl_value = QtWidgets.QSlider(Dialog)
        self.sl_value.setGeometry(QtCore.QRect(220, 120, 161, 31))
        self.sl_value.setOrientation(QtCore.Qt.Horizontal)
        self.sl_value.setObjectName("sl_value")
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

# file main.py
class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.settings = QSettings("COMPANY_NAME", 'APPLICATION_NAME')

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())