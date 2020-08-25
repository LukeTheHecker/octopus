import numpy as np


class Callbacks:
    def __init__(self):
        self.present = False


    def presentToggle(self, event):
        self.present = not self.present
        print(f'self.present = {self.present}')




# Lets design a button