from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from plot import MplCanvas
import numpy as np
from workers import *

class MainWindow:
    ''' Main Window of the Octopus Neurofeedback App. '''
    def __init__(self):

        
        # Create App Window
        # self.mainWidget = QWidget()
        # self.setCentralWidget(self.mainWidget)
        # Icon
        self.setWindowIcon(QIcon('assets/octoicon.svg'))
        # label = QLabel(self)
        # pixmap = QPixmap('assets/octoicon.svg')
        # label.setPixmap(pixmap)

        # Title
        self.setWindowTitle('Octopus Neurofeedback')
        # Data monitor Graph
        self.graphWidget1 = pg.PlotWidget()
        
        pen = pg.mkPen(color='r', width=2)
        self.curve1 = self.graphWidget1.plot(pen=pen)
        # self.curve1.setData([1, 2, 3, 4], [5, 7, 4, 1])
        # Styling
        # self.graphWidget1.plotItem.getAxis('left').setPen(pen)
        # self.graphWidget1.plotItem.getAxis('bottom').setPen(pen)
        # self.graphWidget1.setBackground((255, 255, 255))
        # self.curve1.setData([1, 2, 3], [3, 3, 2], width=0.1)
        # font=QFont("Times", 10)
        # font.setPixelSize(10)
        # self.graphWidget1.getAxis("bottom").setStyle(tickFont = font)
        # self.graphWidget1.getAxis("bottom").setStyle(tickTextOffset = 20)
        # labelstyle = {'color': (0, 0, 0), 'font-size': '14pt'}
        # self.graphWidget1.getAxis("bottom").setLabel("text", units='mV', **labelstyle)
        # self.graphWidget1.getAxis("left").setStyle(tickFont = font)
        # self.graphWidget1.getAxis("left").setStyle(tickTextOffset = 20)

        # Title
        self.title = QLabel()
        self.title.setText("Lag")
        self.title.setFont(QFont("Times", 12))
        # Bottom Graph
        self.MplCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        # self.MplCanvas.ax.hist(np.random.randn(1000))
        # Add label
        self.textBox = QLabel()
        self.textBox.setText("State=")
        self.textBox.setFont(QFont("Times", 14))
        # Add buttons
        self.buttonPresentationcontrol = QPushButton("Allow")
        self.buttonPresentationcontrol.setStyleSheet("background-color: red")
        self.buttonQuit = QPushButton("Quit")
        self.buttonforward = QPushButton("->")
        self.buttonbackwards = QPushButton("<-")
        self.buttonEOGcorrection = QPushButton("EOG Correction")
        

        self.buttonConnectRDA = QPushButton("Connect RDA")
        self.buttonConnectLibet = QPushButton("Connect Libet")

        
        
        # Layout
        self.layout = QGridLayout()
        # Button Group
        button_layout = QGridLayout()
        button_layout.addWidget(self.buttonPresentationcontrol, 0, 0, 1, 3)
        button_layout.addWidget(self.buttonQuit, 1, 2)
        button_layout.addWidget(self.buttonforward, 1, 1)
        button_layout.addWidget(self.buttonbackwards, 1, 0)
        button_layout.addWidget(self.buttonConnectRDA, 2, 1)
        button_layout.addWidget(self.buttonConnectLibet, 2, 2)
        button_layout.addWidget(self.buttonEOGcorrection, 2, 0)

        # Plots title and textbox
        self.layout.addWidget(self.title, 0, 0, 1, 1)  # row pos, col pos, row span, col span
        self.layout.addWidget(self.graphWidget1, 1, 0,)
        self.layout.addWidget(self.MplCanvas, 2, 0)
        self.layout.addWidget(self.textBox, 1, 2)
        self.layout.addLayout(button_layout, 2, 2)
        self.layout.setColumnStretch(0, 3)
        self.layout.setColumnStretch(1, 0.5)
        self.layout.setRowStretch(0, 0.5)


        box = QGroupBox(self)
        box.setLayout(self.layout)
        self.setCentralWidget(box)
        # self.mainWidget.setLayout(self.layout)
    

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
        self.parent.run(settings)


class SelectChannels(QWidget):
    def __init__(self, octopus, parent=None):
        super().__init__(parent)
        
        self.octopus = octopus
        channelnames = self.octopus.gatherer.channelNames
        
        self.layout = QVBoxLayout()
        self.cb1 = QComboBox()
        self.cb2 = QComboBox()
        self.buttonGO = QPushButton("GO")
        

        for channelname in channelnames:
            self.cb1.addItem(channelname)
            self.cb2.addItem(channelname)

        self.layout.addWidget(self.cb1)
        self.layout.addWidget(self.cb2)
        self.layout.addWidget(self.buttonGO)

        
        

        

        self.buttonGO.pressed.connect(self.startThread)


        self.setLayout(self.layout)
        self.setWindowTitle("Select channels for EOG correction")

    def startThread(self):
        worker = EOGWorker(self.octopus.EOGcorrection, self.cb1.currentText(), self.cb2.currentText())
        worker.signals.result.connect(self.octopus.plot_eog_results)  
        print("Starting EOG Correction...")
        self.octopus.threadpool.start(worker)

        
  