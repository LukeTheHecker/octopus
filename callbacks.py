import numpy as np


class Callbacks:
    def __init__(self):
        self.state = False
        self.quit = False

    def presentToggle(self, event):
        self.state = not self.state
        print(f'self.state = {self.state}')




# Lets design a button