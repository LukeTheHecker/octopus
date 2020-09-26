from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time




class InputDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent = parent
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        self.layout = QFormLayout()
        button_box  = QDialogButtonBox(QDialogButtonBox.Ok)

        self.SubjectID = QLineEdit("", self)
        self.channelOfInterestName = QLineEdit("RP", self)
        self.SCPTrialDuration = QLineEdit("2.5", self)
        self.SCPBaselineDuration = QLineEdit("0.25", self)
        self.histCrit = QLineEdit("5", self)
        self.secondInterviewDelay = QLineEdit("5", self)
        self.blindedAxis = QCheckBox(self)
        self.blindedAxis.setChecked(True)


        self.layout.addRow("User ID", self.SubjectID)
        self.layout.addRow("SCP Channel", self.channelOfInterestName)
        verticalSpacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(verticalSpacer)
        self.layout.addRow("SCP dur in seconds", self.SCPTrialDuration)
        self.layout.addRow("SCP baseline dur in seconds", self.SCPBaselineDuration)
        self.layout.addRow("Histogram Criterion", self.histCrit)
        self.layout.addRow("Delay to 2nd Interview", self.secondInterviewDelay)
        self.layout.addRow("Blinding", self.blindedAxis)
        
        # self.layout.addRow('',QSpacerItem())
        self.layout.addWidget(button_box)


        self.mainWidget.setLayout(self.layout)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def getInputs(self):
        settings = {'SubjectID': self.SubjectID.text(),
                    'channelOfInterestName': self.channelOfInterestName.text(),
                    'SCPTrialDuration': self.SCPTrialDuration.text(),
                    'SCPBaselineDuration': self.SCPBaselineDuration.text(),
                    'histCrit': self.histCrit.text(),
                    'secondInterviewDelay': self.secondInterviewDelay.text(),
                    'blindedAxis': self.blindedAxis.isChecked()}
        return settings

    def accept(self):
        self.close()
        self.checkEntries()

    def reject(self):
        self.close()

    def checkEntries(self):
        settings = self.getInputs()
        for key, item in settings.items():
            if item == '':
                self.parent.open_settings_gui()
                return
        # All entries are there!
        self.parent.insert_settings(settings)


