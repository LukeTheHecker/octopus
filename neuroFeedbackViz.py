import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

''' The following functions are animations that are bound to the BaseNeuroFeedback 
class and they expect the result of the BaseNeuroFeedback::update method as input argument. 

Structure:
----------
result : tuple, with items (canvas, score, cal):
->  canvas : Matplotlib Canvas object, canvas to project the visualization on
    score : float, calculated neurofeedback score
    cal : tuple, with items (minval, maxval, medianval), corresponding to
    ->  minval : float, showing the lowest value observed during calibration
        maxval : float, showing the highest value observed during calibration
        medianval : float, median value of calibration
'''

def BarPlotAnimation(result):
    '''Bar Plot Animation.'''
    # plot the frequency band power on a canvas
    canvas, score, cal = result
    minval, maxval, medianval = cal
    ylim = (minval, maxval)
    tolerance = 1.5 * (maxval/medianval)
    # Clear axis
    canvas.ax.clear()
    canvas.ax.set_ylim((0, tolerance))
    # Transform Scores
    score_rel = score/medianval

    df = pd.DataFrame({'x': [0], 'score_rel': [score_rel]})
    sns.barplot(x='x', y='score_rel', ax=canvas.ax, data=df)
    canvas.ax.axhline(1, ls='-', color='black')
    
    canvas.ax.set_ylabel('Baseline ratio')
    canvas.draw()

def circleAnimation(result):
    '''Circle radius animation.'''
    canvas, score, cal = result
    minval, maxval, medianval = cal
    ylim = (minval, maxval)

    pos = (0, 0)  # position of circle center
    tolerance = 3 * (maxval/medianval)

    # Clear axis
    canvas.ax.clear()
    canvas.ax.axis('equal')
    # Transform score to percentage of calibaration median:
    score_rel = score/medianval
    # ylim_rel = [i / medianval for i in ylim]


    circle1 = plt.Circle(pos, score_rel, color='r')
    canvas.ax.add_artist(circle1)
    canvas.ax.set_ylim((pos[0] - tolerance, pos[0] + tolerance))
    canvas.ax.set_xlim((pos[0] - tolerance, pos[0] + tolerance))
    
    canvas.draw()