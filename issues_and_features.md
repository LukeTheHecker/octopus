# Current Issues



## I2: Form on startup does not know which channels are available
### Description:
When octopus starts it asks for SCP channel and reference channels, however these are sometimes unknon, sometimes no extra reference channel may be required. 

### Solution:
* Give the user more options by allowing no reference channels
* Be smart and check if "Cz" is present as SCP channel, otherwise auto-select a channel that is present such that it technically works.

# Feature Reqests

## F1: Neurofeedback
* Make sure the neurofeedback modules work nice and modular
* Add calibration button
* Implement the live source imaging neurofeedback

## F2: UI Design
* Add basic recording parameters as text on the UI:
1000Hz - 32 Channels - 



# Qualitiy Assurance
## QA1:
Ensure blinding works as intended and create a new blinding template

## QA2:
Perform technical pilot with yourself as participant

## QA3:
What was the deal with the eye artifact removal? How can you verify that it works?


# Solved
## I1: Quit Button dysfunctional
### Description 
When pressing quit the program halts and throws an error that some connection is not correct.

## F3: Folder structure
Separate code repository from general files like you do for a python package.