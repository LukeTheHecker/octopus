# Octopus Neurofeedback

The Octupus Neurofeedback is coded in Python 3 using PyQt5 and uses signals from the brain vision actiCHamp [Remote Data Access](https://pressrelease.brainproducts.com/real-time-eeg/) functionality.

This program is used for reading EEG data and plotting/ processing it. This can be used as a basis for neurofeedback only if 50-100 ms of delay (caused by RDA) is acceptable (go [here](https://pressrelease.brainproducts.com/real-time-eeg/) for an explanation).

![Octopus Neurofeedback](https://github.com/LukeTheHecker/rda_libet/blob/master/assets/Octopuspic.png?raw=true)


# Intended Use
If you are using an EEG amplifier by Brain Products and would like to set up a live data analysis, visualization or neurofeedback paradigm then this repository may help you as an entry point. However, I want to disclose that some programming knowledge in python is necessary to customize the code to meet your needs. 

## Get started

* Install [Anaconda/Miniconda](https://www.anaconda.com/) 2 or 3
* create environment using requirements.txt:  
`conda create --name octo --file requirements.txt`
* Activate the environment: `conda activate octo`
* Clone this repository using `git clone https://github.com/LukeTheHecker/octopus.git` or download the [ZIP file](https://github.com/LukeTheHecker/octopus/archive/master.zip).
* go to the cloned directory using `cd octopus`
* Execute the `main.py` from your conda environment:

```
conda activate octo
python main.py
```

## Acknowledgements:  
Octopus icon made by [Freepik](https://www.flaticon.com/authors/freepik) from [Flaticon](https://www.flaticon.com/).

## Developers:
[Lukas Hecker](https://twitter.com/HeckerOfficial) (mailto:lukas_hecker@web.de)  
Marianne Hense

## Group:  
Department of Psychosomatic Medicine and Psychotherapy  
Medical Faculty Medical Center – University of Freiburg,    
Freiburg, Germany

## Funding:
Special thanks goes to [Bial Foundation](https://www.bial.com/com/bial-foundation/grants/) for funding the corresponding project.
