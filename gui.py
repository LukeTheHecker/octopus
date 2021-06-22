from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import callbacks
import pyqtgraph as pg
import plot
import workers
import json

class MainWindow(QMainWindow):
    ''' Main Window of the Octopus Neurofeedback App. '''
    def __init__(self):

        super(MainWindow, self).__init__()
        self.setFixedSize(1200, 720)

        # Callbacks
        self.callbacks = callbacks.Callbacks(self)
        # Create App Window
        # Menu
        menubar = self.menuBar()
        # File - Dropdown
        file_menu = menubar.addMenu('File')

        load_state_button = QAction('Load state', self)
        file_menu.addAction(load_state_button)
        # load_state_button.connect(self.callbacks.load_state)

        save_state_button = QAction('Save state', self)
        file_menu.addAction(save_state_button)
        # save_state_button.connect(self.callbacks.save_state)

        self.quit_button = QAction('Quit', self)
        self.quit_button.triggered.connect(self.quit)
        # self.quit_button.triggered.connect(self.helloworld)
        
        file_menu.addAction(self.quit_button)
        

        # Edit - Dropdown
        edit_menu = menubar.addMenu('Edit')

        settingsButton = QAction('Settings', self)
        edit_menu.addAction(settingsButton)
        settingsButton.triggered.connect(self.callbacks.open_settings)

        # Connections - Dropdown
        connections_menu = menubar.addMenu('Connections')
        connect_rda_button = QAction('Connect RDA', self)
        connections_menu.addAction(connect_rda_button)
        connect_libet_button = QAction('Connect Libet', self)
        connections_menu.addAction(connect_libet_button)

        
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
        self.graphWidget1.enableAutoRange('y', False)
        pen = pg.mkPen(color='r', width=1)
        self.curve1 = self.graphWidget1.plot(pen=pen)
        # Title
        self.title = QLabel()
        self.title.setText("Lag")
        self.title.setFont(QFont("Times", 12))
        # Bottom Graph
        self.MplCanvas = plot.MplCanvas(self, width=5, height=4, dpi=100)
        # Add label
        self.textBox = QLabel()
        self.textBox.setText("State=")
        self.textBox.setFont(QFont("Times", 14))
        # Add channel dropdown
        self.channel_dropdown = QComboBox()
        # Add buttons
        self.buttonPresentationcontrol = QPushButton("Disabled")
        self.buttonPresentationcontrol.setStyleSheet("background-color: red")
        self.buttonQuit = QPushButton("Quit")
        self.buttonforward = QPushButton("->")
        self.buttonbackwards = QPushButton("<-")
        self.buttonEOGcorrection = QPushButton("EOG Correction")
        self.buttonConnectRDA = QPushButton("Connect RDA")
        self.buttonConnectLibet = QPushButton("Connect Libet")
        self.buttonToggleEOGcorrection = QPushButton("EOG On/Off")
        
        # Button Group
        button_layout = QGridLayout()
        button_layout.addWidget(self.buttonPresentationcontrol, 0, 0, 1, 3)
        button_layout.addWidget(self.buttonQuit, 1, 2)
        button_layout.addWidget(self.buttonforward, 1, 1)
        button_layout.addWidget(self.buttonbackwards, 1, 0)
        button_layout.addWidget(self.buttonConnectRDA, 2, 1)
        button_layout.addWidget(self.buttonConnectLibet, 2, 2)
        button_layout.addWidget(self.buttonEOGcorrection, 2, 0)
        button_layout.addWidget(self.buttonToggleEOGcorrection, 3, 0)
        
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
        self.NFCanvas = plot.MplCanvas(self, width=5, height=4, dpi=100)
        self.layoutNF.addWidget(self.NFCanvas, 0, 0)
        self.tabNeuroFeedback.setLayout(self.layoutNF)

        self.setCentralWidget(self.tabs)
        # self.mainWidget.setLayout(self.layout)
    def quit(self):
        print('pressed quit on menu')
        self.quit=True
        self.closeAll()
class InputDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent = parent
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        self.layout = QFormLayout()
        button_box  = QDialogButtonBox(QDialogButtonBox.Ok)

        self.SubjectID = QLineEdit("", self)
        self.channelOfInterestName = QLineEdit("Cz", self)
        self.refChannels = QLineEdit("TP9, TP10", self)
        self.EOGChannelName = QLineEdit("VEOG", self)
        self.SCPTrialDuration = QLineEdit("2.5", self)
        self.SCPBaselineDuration = QLineEdit("0.20", self)
        self.samplingCrit = QLineEdit("5", self)
        self.secondInterviewDelay = QLineEdit("5", self)
        self.blindedAxis = QCheckBox(self)
        self.blindedAxis.setChecked(True)


        self.layout.addRow("User ID", self.SubjectID)
        self.layout.addRow("SCP Channel", self.channelOfInterestName)
        self.layout.addRow("Reference Channels", self.refChannels)
        self.layout.addRow("VEOG Channel", self.EOGChannelName)
        verticalSpacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(verticalSpacer)
        self.layout.addRow("SCP dur in seconds", self.SCPTrialDuration)
        self.layout.addRow("SCP baseline dur in seconds", self.SCPBaselineDuration)
        self.layout.addRow("SCP sampling criterion", self.samplingCrit)
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
                    'EOGChannelName': self.EOGChannelName.text(),
                    'SCPTrialDuration': self.SCPTrialDuration.text(),
                    'SCPBaselineDuration': self.SCPBaselineDuration.text(),
                    'samplingCrit': self.samplingCrit.text(),
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

class SelectChannels(QMainWindow):
    def __init__(self, octopus):
        
        # Check if gatherer is connected at all:
        self.octopus = octopus
        if not self.octopus.gatherer.connected or not hasattr(octopus.gatherer, 'channelNames'):
            print(f'Cannot call EOG Correction since Gather class is not connected.')
            return

        super().__init__(octopus)
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        channelnames = self.octopus.gatherer.channelNames
        
        self.layout = QFormLayout()
        self.text = QLabel()
        self.text.setText('Choose the VEOG channel')
        self.cb1 = QComboBox()
        self.buttonGO = QPushButton("GO")

        for channelname in channelnames:
            self.cb1.addItem(channelname)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.cb1)
        self.layout.addWidget(self.buttonGO)

        self.buttonGO.pressed.connect(self.startThread)
        self.mainWidget.setLayout(self.layout)

        # self.setLayout(self.layout)
        self.setWindowTitle("Select channels for EOG correction")

    def startThread(self):
        worker = workers.EOGWorker(self.octopus.EOGcorrection, self.cb1.currentText())
        worker.signals.result.connect(self.octopus.plot_eog_results)  
        print("Starting EOG Correction...")
        self.octopus.threadpool.start(worker)
        self.close()

    def accept(self):
        self.close()

    def reject(self):
        self.close()

class LoadDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent = parent
        self.filename = "states/" + parent.SubjectID + '.json'

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        title = f'Alert!'
        self.setWindowTitle(title)
        
        self.buttonBox  = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.No)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        label = QLabel()
        text = f"ID >>>{self.parent.SubjectID}<<< already exists. Load data?"
        label.setText(text)

        self.layout = QVBoxLayout()
        self.layout.addWidget(label)
        self.layout.addWidget(self.buttonBox)


        self.mainWidget.setLayout(self.layout)
        
        # Dont allow to close window
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
   
    def getInputs(self):
        settings = {'SubjectID': self.SubjectID.text(),
                    'channelOfInterestName': self.channelOfInterestName.text(),
                    'refChannels': self.refChannels.text(),
                    'EOGChannelName': self.EOGChannelName.text(),
                    'SCPTrialDuration': self.SCPTrialDuration.text(),
                    'SCPBaselineDuration': self.SCPBaselineDuration.text(),
                    'samplingCrit': self.samplingCrit.text(),
                    'secondInterviewDelay': self.secondInterviewDelay.text(),
                    'blindedAxis': self.blindedAxis.isChecked()}
        return settings

    def accept(self):
        with open(self.filename, 'r') as f:
            json_file_read = json.load(f)
        
        State = json.loads(json_file_read)

        self.parent.hist_monitor.scpAveragesList = State['scpAveragesList']
        self.parent.current_state = State['current_state']
        self.parent.SubjectID = State['SubjectID']
        self.parent.cond_order = State['cond_order']
        self.parent.d_est = State['d_est']
        self.close()

    def reject(self):
        self.parent.save()
        self.close()

    def checkEntries(self):
        settings = self.getInputs()
        for key, item in settings.items():
            if item == '':
                self.parent.open_settings_gui()
                return
        # All entries are there!
        self.parent.run(settings)       

