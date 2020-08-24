
import numpy as np
import Tkinter as tk

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

root = tk.Tk()

fig = plt.figure(1)
ax = fig.add_subplot(221)

t = np.arange(0.0,3.0,0.01)
s = np.sin(np.pi*t)
ax.plot(t,s)

ax2 = fig.add_subplot(223)

t = np.arange(0.0,3.0,0.01)
s = np.sin(np.pi*t+0.4)
ax2.plot(t,s)



canvas = FigureCanvasTkAgg(fig, master=root)
plot_widget = canvas.get_tk_widget()

def update():
    s = np.cos(np.pi*t)
    ax2.plot(t,s)
    #d[0].set_ydata(s)
    fig.canvas.draw()

plot_widget.grid(row=0, column=0)
tk.Button(root,text="Update",command=update).grid(row=1, column=0)
root.mainloop()