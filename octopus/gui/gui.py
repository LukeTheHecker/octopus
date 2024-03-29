from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
# import callbacks
import pyqtgraph as pg
from octopus import plot
from octopus import workers
import json
import numpy as np
import time

STANDARD_FONT = 'Cambria'
SIZE_POLICY = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
class MainWindow(QMainWindow):
    ''' Main Window of the Octopus Neurofeedback App. '''
    def __init__(self):

        super(MainWindow, self).__init__()
        self.setFixedSize(1200, 720)

        self.eog_toggle = True
        self.eog_toggle_text = ['EOG: Off', 'EOG: On']

        # Create App Window
        
        #========================================#
        # Menu
        menubar = self.menuBar()
        # File - Menu
        file_menu = menubar.addMenu('File')

        self.load_state_button = QAction('Load state', self)
        file_menu.addAction(self.load_state_button)

        self.save_state_button = QAction('Save state', self)
        file_menu.addAction(self.save_state_button)

        self.quit_button = QAction('Quit', self)
        file_menu.addAction(self.quit_button)
        
        # Edit - Menu
        edit_menu = menubar.addMenu('Edit')

        self.settingsButton = QAction('Settings', self)
        edit_menu.addAction(self.settingsButton)
        
        # Connections - Menu
        connections_menu = menubar.addMenu('Connections')

        self.connect_rda_button = QAction('Connect RDA', self)
        connections_menu.addAction(self.connect_rda_button)

        self.connect_libet_button = QAction('Connect Libet', self)
        connections_menu.addAction(self.connect_libet_button)

        # Tools - Menu
        tools_menu = menubar.addMenu('Tools')
        self.eog_correction_button = QAction('EOG Correction', self)
        tools_menu.addAction(self.eog_correction_button)

        self.reset_d_est_button = QAction('Reset EOG correction', self)
        tools_menu.addAction(self.reset_d_est_button)
        
        self.toggle_eog_button = QAction('Toggle EOG correction', self)
        tools_menu.addAction(self.toggle_eog_button)

        #========================================#        

        # Tabs
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabMain = QGroupBox(self)
        self.tabMain.setSizePolicy(SIZE_POLICY)
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
        pen = pg.mkPen(color='r', width=1.)
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
        self.textBox.setFont(QFont(STANDARD_FONT, 14))
        
        # Add channel dropdown
        self.channel_dropdown = QComboBox()
        # Add buttons
        # Button for presentation control
        self.buttonColor = ["background-color: red", "background-color: green"]
        self.permission_statement = ['Disabled', 'Enabled']
        self.allow_presentation = False
        self.buttonPresentationcontrol = QPushButton("Disabled")
        self.buttonPresentationcontrol.setStyleSheet("background-color: red")
        # Buttons for state changes:
        self.buttonforward = QPushButton("->")
        self.buttonbackwards = QPushButton("<-")
        self.amp_info_text = QLabel()
        self.amp_info_text.setText("SF: , Chans: ")
        self.amp_info_text.setFont(QFont(STANDARD_FONT, 14))

        
        # Button Group
        button_layout = QGridLayout()
        button_layout.addWidget(self.buttonPresentationcontrol, 0, 0, 1, 2)
        # button_layout.addWidget(self.buttonQuit, 1, 2)
        button_layout.addWidget(self.buttonforward, 1, 1, 1, 1)
        button_layout.addWidget(self.buttonbackwards, 1, 0, 1, 1)
        button_layout.addWidget(self.amp_info_text, 2, 0, 1, 2)


        # Lag and channel dropdown thing
        second_head_layout = QGridLayout()
        second_head_layout.addWidget(self.title, 0, 0)
        second_head_layout.addWidget(self.channel_dropdown, 0, 1)


        # Connect actions to buttons:
        self._connectActions()

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

    def _connectActions(self):
        # Connect buttons/ menu with actions (methods/functions)
        
        # Menu Buttons
        self.quit_button.triggered.connect(self.quit)
        self.load_state_button.triggered.connect(self.load)
        self.save_state_button.triggered.connect(self.save)
        self.settingsButton.triggered.connect(self.open_settings_gui)
        self.connect_rda_button.triggered.connect(self.set_info)
        self.connect_libet_button.triggered.connect(self.connect_libet)
        self.eog_correction_button.triggered.connect(self.eog_correction_selectChannel)
        self.reset_d_est_button.triggered.connect(self.reset_d_est)
        self.toggle_eog_button.triggered.connect(self.toggle_eog_correction)
        # On-GUI Buttons
        self.buttonPresentationcontrol.pressed.connect(self.presentToggle)
        self.buttonforward.pressed.connect(self.stateforward)
        self.buttonbackwards.pressed.connect(self.statebackwards)
        self.channel_dropdown.activated.connect(self.change_view_channel)
     
    def open_settings_gui(self):
        dialog = InputDialog(self)
        dialog.show()


    def presentToggle(self):
        self.allow_presentation = not self.allow_presentation
        self.change_allow_button()
    
    def quit(self):
        self.quit=True
        self.closeAll()
    

    def stateforward(self):
        self.stateChange = 1
        self.switchState()
        
    def statebackwards(self):
        self.stateChange = -1
        self.switchState()
    
    def switchState(self):
        new_state = np.clip(self.current_state + self.stateChange, a_min = 0, a_max = 5)
        # If state hasnt actually changed return
        if new_state == self.current_state:
            return
        
        # Otherwise..
        # Forbid experiment and change button color + text if state actually changed
        self.allow_presentation = False
        self.change_allow_button()
        # Save new state
        self.current_state = new_state
        self.stateChange = 0

    def change_allow_button(self):
        i = int(self.allow_presentation)
        self.buttonPresentationcontrol.setStyleSheet(self.buttonColor[i])
        self.buttonPresentationcontrol.setText(self.permission_statement[i])

    

    
    def connect_libet(self):
        n_total_fails_allowed = 5
        if hasattr(self, 'internal_tcp'):
            if not self.internal_tcp.connected:
                print(f'Attempting connection to {self.internal_tcp.IP} {self.internal_tcp.port}...')
                self.internal_tcp.accept_connection()
                if self.internal_tcp.connected:
                    n_fails = 0
                    while n_fails < n_total_fails_allowed:
                        try:
                            self.threadpool.start(self.worker_communication)
                            break
                        except:
                            time.sleep(1)


    def eog_correction_selectChannel(self):
        if self.gatherer.connected:
            print('Starting EOG Correction')
            mydialog = SelectChannels(self)
            mydialog.show()
        else:
            print('EOG correction is not possible until gatherer is connected to RDA.')
    
    def toggle_eog_correction(self):
        ''' Toggle EOG correction on/off'''
        # Toggle EOG correction
        self.eog_toggle = not self.eog_toggle
        # Change Button label accordingly
        self.toggle_eog_button.setText(self.eog_toggle_text[int(self.eog_toggle)])
        # Change Button color accordingly
        # self.toggle_eog_button.setStyleSheet(self.buttonColor[int(self.eog_toggle)])

    def reset_d_est(self):
        self.d_est = np.zeros(len(self.d_est))

    def change_view_channel(self):
        print(f'Changed viewchannel for data monitor from {self.viewChannel} to {self.channel_dropdown.currentText()}')
        self.viewChannel = self.channel_dropdown.currentText()

class InputDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent = parent
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.layout = QFormLayout()
        button_box  = QDialogButtonBox(QDialogButtonBox.Ok)

        self.settings = None
        self.SubjectID = QLineEdit("", self)
        self.channelOfInterestName = QLineEdit("Cz", self)
        self.refChannels = QLineEdit("TP9, TP10", self)
        self.EOGChannelName = QLineEdit("VEOG", self)
        self.SCPTrialDuration = QLineEdit("2.5", self)
        self.SCPBaselineDuration = QLineEdit("0.20", self)
        self.samplingCrit = QLineEdit("15", self)
        self.secondInterviewDelay = QLineEdit("5", self)
        self.blindedAxis = QCheckBox(self)
        self.blindedAxis.setChecked(True)

        self.simulated_data = QCheckBox(self)
        self.simulated_data.setChecked(False)

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
        self.layout.addRow("Simulated Data", self.simulated_data)
        
        
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
                    'blindedAxis': self.blindedAxis.isChecked(),
                    'simulated_data': self.simulated_data.isChecked()
                    }
        return settings

    def accept(self):
        ''' Callback for the "Accept" button of the Input Dialog.
        '''
        self.close()
        self.checkEntries()
        
        

    def reject(self):
        ''' Callback for the "Reject" button of the Input Dialog.
        '''
        self.close()

    def checkEntries(self):
        settings = self.getInputs()
        for key, item in settings.items():
            if item == '':
                self.parent.open_settings_gui()
                return
        # All entries are there!
        self.parent.saveSettings(settings)
        self.parent.run()

class SelectChannels(QMainWindow):
    def __init__(self, model):
        
        # Check if gatherer is connected at all:
        self.model = model
        if not self.model.gatherer.connected or not hasattr(model.gatherer, 'channelNames'):
            print(f'Cannot call EOG Correction since Gather class is not connected.')
            return

        super().__init__(model)
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        channelnames = self.model.gatherer.channelNames
        
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
        worker = workers.EOGWorker(self.model.eog_correction, self.cb1.currentText())
        worker.signals.result.connect(self.model.plot_eog_results)  
        print("Starting EOG Correction...")
        self.model.threadpool.start(worker)
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
        title = f'Obacht!'
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

