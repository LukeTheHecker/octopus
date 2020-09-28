import numpy as np


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

    def presentToggle(self):
        self.allow_presentation = not self.allow_presentation
        self.ChangeAllowButton()

    def quitexperiment(self):
        print("pressed")
        self.quit=True
        self.octopus.current_state = 5

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
            return
        if result:
            self.octopus.handleChannelIndex() 
    
    def connectLibet(self):
        if hasattr(self.octopus, 'internal_tcp'):
            self.octopus.internal_tcp.connect()
# Lets design a button