import numpy as np
import random
from gui import SelectChannels


class Callbacks:
    def __init__(self, octopus):
        self.allow_presentation = False
        self.permission_statement = ['Allow', 'Forbid']
        self.buttonColor = ["background-color: red", "background-color: green"]
        self.quit = False
        self.stateChange = 0
        self.octopus = octopus

        self.octopus.buttonPresentationcontrol.pressed.connect(self.presentToggle)
        self.octopus.buttonQuit.pressed.connect(self.quitexperiment)
        self.octopus.buttonforward.pressed.connect(self.stateforward)
        self.octopus.buttonbackwards.pressed.connect(self.statebackwards)
        self.octopus.buttonConnectRDA.pressed.connect(self.connectRDA)
        self.octopus.buttonConnectLibet.pressed.connect(self.connectLibet)
        self.octopus.buttonEOGcorrection.pressed.connect(self.EOGcorrection)
        self.octopus.channel_dropdown.currentIndexChanged.connect(self.change_view_channel)

    def presentToggle(self):
        self.allow_presentation = not self.allow_presentation
        self.ChangeAllowButton()

    def quitexperiment(self):
        print("pressed")
        self.quit=True
        self.octopus.closeAll()

    def stateforward(self):
        self.stateChange = 1
        self.switchState()
        
    def statebackwards(self):
        self.stateChange = -1
        self.switchState()
    
    def switchState(self):
        new_state = np.clip(self.octopus.current_state + self.stateChange, a_min = 0, a_max = 5)
        # If state hasnt actually changed return
        if new_state == self.octopus.current_state:
            return
        
        # Otherwise..
        # Forbid experiment and change button color + text if state actually changed
        self.allow_presentation = False
        self.ChangeAllowButton()
        # Save new state
        self.octopus.current_state = new_state
        self.stateChange = 0

    def ChangeAllowButton(self):
        i = int(self.allow_presentation)
        self.octopus.buttonPresentationcontrol.setStyleSheet(self.buttonColor[i])
        self.octopus.buttonPresentationcontrol.setText(self.permission_statement[i])

    def connectRDA(self):
        if hasattr(self.octopus, 'gatherer'):
            result = self.octopus.gatherer.connect()
        else:
            return False

        if result:
            self.octopus.gatherer.refChannels = self.octopus.refChannels
            self.octopus.EOGChannelIndex = self.octopus.gatherer.channelNames.index(self.octopus.EOGChannelName)
            self.octopus.d_est = np.zeros(len(self.octopus.gatherer.channelNames))
            self.octopus.handleChannelIndex() 
            self.octopus.fillChannelDropdown()
            self.octopus.init_plots()
            # self.octopus.startNeurofeedbacks()
            
        return result
    
    def connectLibet(self):
        if hasattr(self.octopus, 'internal_tcp'):
            if not self.octopus.internal_tcp.connected:
                print(f'Attempting connection to {self.octopus.internal_tcp.IP} {self.octopus.internal_tcp.port}...')
                self.octopus.internal_tcp.accept_connection()
                if self.octopus.internal_tcp.connected:
                    self.octopus.threadpool.start(self.worker_communication)

    def EOGcorrection(self):
        if self.octopus.gatherer.connected:
            print('Starting EOG Correction')
            self.mydialog = SelectChannels(self.octopus)
            self.mydialog.show()
        else:
            print('EOG correction is not possible until gatherer is connected to RDA.')

    def change_view_channel(self):
        print(f'Changed viewchannel for data monitor from {self.octopus.viewChannel} to {self.octopus.channel_dropdown.currentText()}')
        self.octopus.viewChannel = self.octopus.channel_dropdown.currentText()
        