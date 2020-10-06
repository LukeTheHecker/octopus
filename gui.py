from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from plot import MplCanvas
from workers import *

class MainWindow(QMainWindow):
    ''' Main Window of the Octopus Neurofeedback App. '''
    def __init__(self):

        super(MainWindow, self).__init__()
        self.setFixedSize(1000, 600)
        # Create App Window
        # Tabs
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabMain = QGroupBox(self)
        self.tabNeuroFeedback = QGroupBox(self)
        self.tabs.addTab(self.tabMain,"Main")
        self.tabs.addTab(self.tabNeuroFeedback,"Neurofeedback")
        # Icon
        self.setWindowIcon(QIcon('assets/octoicon.svg'))

        # Main Tab
        # Title
        self.setWindowTitle('Octopus Neurofeedback')
        # Data monitor Graph
        self.graphWidget1 = pg.PlotWidget()
        pen = pg.mkPen(color='r', width=2)
        self.curve1 = self.graphWidget1.plot(pen=pen)
        # Title
        self.title = QLabel()
        self.title.setText("Lag")
        self.title.setFont(QFont("Times", 12))
        # Bottom Graph
        self.MplCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add label
        self.textBox = QLabel()
        self.textBox.setText("State=")
        self.textBox.setFont(QFont("Times", 14))
        # Add channel dropdown
        self.channel_dropdown = QComboBox()
        # Add buttons
        self.buttonPresentationcontrol = QPushButton("Allow")
        self.buttonPresentationcontrol.setStyleSheet("background-color: red")
        self.buttonQuit = QPushButton("Quit")
        self.buttonforward = QPushButton("->")
        self.buttonbackwards = QPushButton("<-")
        self.buttonEOGcorrection = QPushButton("EOG Correction")
        self.buttonConnectRDA = QPushButton("Connect RDA")
        self.buttonConnectLibet = QPushButton("Connect Libet")
        
        # Button Group
        button_layout = QGridLayout()
        button_layout.addWidget(self.buttonPresentationcontrol, 0, 0, 1, 3)
        button_layout.addWidget(self.buttonQuit, 1, 2)
        button_layout.addWidget(self.buttonforward, 1, 1)
        button_layout.addWidget(self.buttonbackwards, 1, 0)
        button_layout.addWidget(self.buttonConnectRDA, 2, 1)
        button_layout.addWidget(self.buttonConnectLibet, 2, 2)
        button_layout.addWidget(self.buttonEOGcorrection, 2, 0)
        # Lag and channel dropdown thing
        second_head_layout = QGridLayout()
        second_head_layout.addWidget(self.title, 0, 0)
        second_head_layout.addWidget(self.channel_dropdown, 0, 1)
        # button_layout2 = QGridLayout()
        # button_layout2.addWidget(self.buttonPresentationcontrol, 0, 0, 1, 3)
        # button_layout2.addWidget(self.buttonQuit, 1, 2)

        # Layout
        self.layout = QGridLayout()
        self.layout.addLayout(second_head_layout, 0, 0)  # row pos, col pos, row span, col span
        self.layout.addWidget(self.graphWidget1, 1, 0,)
        self.layout.addWidget(self.MplCanvas, 2, 0)
        self.layout.addWidget(self.textBox, 1, 2)
        self.layout.addLayout(button_layout, 2, 2)
        self.layout.setColumnStretch(0, 3)
        self.layout.setColumnStretch(1, 0.5)
        self.layout.setRowStretch(0, 0.5)

        self.tabMain.setLayout(self.layout)

        # Neurofeedback Tab
        self.layoutNF = QGridLayout()
        self.barGraph = MplCanvas(self, width=5, height=4, dpi=100)
        self.layoutNF.addWidget(self.barGraph, 0, 0)
        self.tabNeuroFeedback.setLayout(self.layoutNF)


        
        

        
        self.setCentralWidget(self.tabs)
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
        self.refChannels = QLineEdit("TP9, TP10", self)
        self.SCPTrialDuration = QLineEdit("2.5", self)
        self.SCPBaselineDuration = QLineEdit("0.20", self)
        self.histCrit = QLineEdit("5", self)
        self.secondInterviewDelay = QLineEdit("5", self)
        self.blindedAxis = QCheckBox(self)
        self.blindedAxis.setChecked(True)


        self.layout.addRow("User ID", self.SubjectID)
        self.layout.addRow("SCP Channel", self.channelOfInterestName)
        self.layout.addRow("Reference Channels", self.refChannels)
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

        # Action when closing window
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        # quit = QAction("Quit", self)
        # quit.triggered.connect(self.show)
        # quit.triggered.connect(self.show)

    def getInputs(self):
        settings = {'SubjectID': self.SubjectID.text(),
                    'channelOfInterestName': self.channelOfInterestName.text(),
                    'refChannels': self.refChannels.text(),
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
        
        # Check if gatherer is connected at all:
        self.octopus = octopus
        if not self.octopus.gatherer.connected or not hasattr(octopus.gatherer, 'channelNames'):
            print(f'Cannot call EOG Correction since Gather class is not connected.')
            return

        super().__init__(parent)

        channelnames = self.octopus.gatherer.channelNames
        
        self.layout = QVBoxLayout()
        self.text = QLabel()
        self.text.setText('Choose the VEOG channel')
        self.cb1 = QComboBox()
        # self.cb2 = QComboBox()
        self.buttonGO = QPushButton("GO")

        for channelname in channelnames:
            self.cb1.addItem(channelname)
            # self.cb2.addItem(channelname)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.cb1)
        self.layout.addWidget(self.cb2)
        self.layout.addWidget(self.buttonGO)

        self.buttonGO.pressed.connect(self.startThread)

        self.setLayout(self.layout)
        self.setWindowTitle("Select channels for EOG correction")

    def startThread(self):
        worker = EOGWorker(self.octopus.EOGcorrection, self.cb1.currentText())
        worker.signals.result.connect(self.octopus.plot_eog_results)  
        print("Starting EOG Correction...")
        self.octopus.threadpool.start(worker)

        
  