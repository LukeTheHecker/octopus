import numpy as np


class Callbacks:
    def __init__(self):
        self.allow_presentation = False
        self.permission_statement = ['Allow', 'Forbid']
        self.quit = False
        self.stateChange = 0

    def presentToggle(self):
        self.allow_presentation = not self.allow_presentation

    def quitexperiment(self):
        print("pressed")
        self.quit=True

    def stateforward(self):
        self.stateChange = 1
        
    def statebackwards(self):
        self.stateChange = -1


# Lets design a button