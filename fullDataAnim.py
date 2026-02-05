import pickle
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.ticker import MultipleLocator
import numpy as np
import math


folder = 'Pipe_241_0/'
titleStart = 'Sensor Centre Pos - '
gifName = 'img/SensorCentre'


data = []
dataLin = []
dataLog = []
x = np.linspace(0, 2.41, 64)

with open(folder + 'None.pkl', 'rb') as f:
    fileData = pickle.load(f)

fileData = [val[8] for val in fileData]
fileData = [sum(col)/ len(col) for col in zip(*fileData)]

dataLin.append([(32.0/float(len(x))) * (2**(val/512.0)) for val in fileData])
dataLog.append([(val*20.0*math.log10(2.0))/512.0 + 20.0*math.log10(32.0/float(len(x))) for val in fileData])




for i in range(5,205,5):
    with open(folder + f'{i}.pkl', 'rb') as f:
        fileData = pickle.load(f)
    fileData = [val[8] for val in fileData]
    fileData = [sum(col)/ len(col) for col in zip(*fileData)]

    dataLin.append([(32.0/float(len(x))) * (2**(val/512.0)) for val in fileData])
    dataLog.append([(val*20.0*math.log10(2.0))/512.0 + 20.0*math.log10(32.0/float(len(x))) for val in fileData])

fig, (axLin, axLog) = plt.subplots(1, 2)

title = fig.suptitle("", fontsize=16)

lineLin, = axLin.plot([], [], color = 'blue', label='Linear Scale')
lineLog, = axLog.plot([], [], color = 'red', label='Log Scale')

axLin.set_ylim(min([min(val) for val in dataLin]), max([max(val) for val in dataLin]))
axLog.set_ylim(min([min(val) for val in dataLog]), max([max(val) for val in dataLog]))

axLin.set_xlim(0,2.41)
axLog.set_xlim(0,2.41)

axLin.set_title('Linear Scale')
axLog.set_title('Log Scale')

axLin.set_xlabel('Distance (m)')
axLog.set_xlabel('Distance (m)')
axLin.set_ylabel('Signal Strength')
axLog.set_ylabel('Signal Strength (dB)')


for ax in [axLin, axLog]:
    ax.xaxis.set_major_locator(MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(MultipleLocator(0.1))
    ax.grid(True, which='major', axis='x', linewidth=1)
    ax.grid(True, which='minor', axis='x', linestyle=':', alpha=0.4)

def init():
    lineLin.set_data([],[])
    lineLog.set_data([],[])
    title.set_text("")
    return lineLin, lineLog, title

def animate(i):
    lineLin.set_data(x, dataLin[i])
    lineLog.set_data(x, dataLog[i])
    if i == 0:
        title.set_text(titleStart + "No target")
    else:
        title.set_text(titleStart + f"Target at {i*5}cm Distance")
    return lineLin, lineLog, title

plt.tight_layout(rect=[0, 0, 1, 0.95])

anim = animation.FuncAnimation(fig, animate, init_func=init,
                              frames=len(dataLin), interval=200, blit=False)

#anim.save(gifName + '.gif', writer='pillow')
anim.save(gifName + '.mp4', writer='ffmpeg')
plt.show()