# Octopus Neurofeedback

The Octupus Neurofeedback is coded in Python 3 using PyQt5 and uses signals from the brain vision actiCHamp [Remote Data Access](https://pressrelease.brainproducts.com/real-time-eeg/) functionality.

This program is used for reading EEG data and plotting/ processing it. This can be used as a basic for neurofeedback only if ~100 ms of delay (caused by RDA) is acceptable.

![Octopus Neurofeedback](https://github.com/LukeTheHecker/rda_libet/blob/master/assets/Octopuspic.png?raw=true)

## Get started

* Install Anaconda/Miniconda 2 or 3
* create environment using requirements.txt:  
`conda env create -n octo -f requirements.txt`

* Run the `main.py` to get started:

```
python main.py
```

## Acknowledgements:  
Octopus icon made by [Freepik](https://www.flaticon.com/authors/freepik) from [Flaticon](https://www.flaticon.com/).

## Developers:
Lukas Hecker
Marianne Hense

## Group:  
Department of Psychosomatic Medicine and Psychotherapy  
Medical Faculty Medical Center – University of Freiburg,    
Freiburg, Germany

## Funding:
Special thanks goes to [Bial Foundation](https://www.bial.com/com/bial-foundation/grants/) for funding the corresponding project.