import pickle
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.ticker import MultipleLocator
import numpy as np
import math

with open('Data/Air_241_110.pkl', 'rb') as f:
    data = pickle.load(f)

with open('savedDataNone.pkl', 'rb') as f:
    noiseData = pickle.load(f)

data = [val[8] for val in data]
##Attempt at denoising
#noiseProfile = [0 for val in noiseData[0][8]]
#for val in noiseData:
#    for i in range(len(val[8])):
#        noiseProfile[i] += val[8][i]
#noiseProfile = [val/len(noiseData) for val in noiseProfile]
#
#dataDenoised = [[data[i][j] - noiseProfile[j] for j in range(len(data[i]))] for i in range(len(data))]


dataLinScale = []
dataLogScale = []
for i in range(len(data)):
    x = np.linspace(0, 2.41, len(data[i]))
    dataLinScale.append([(32.0/float(len(x))) * (2**(val/512.0)) for val in data[i]])
    dataLogScale.append([(val*20.0*math.log10(2.0))/512.0 + 20.0*math.log10(32.0/float(len(x))) for val in data[i]])

# Create figure with 4 subplots (2x2 grid)
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Initialize lines for each subplot
line1, = ax1.plot([], [], color='red', label='Original')
line2, = ax2.plot([], [], color='blue', label='Linear Scale')
line3, = ax3.plot([], [], color='green', label='Log Scale')
line4_orig, = ax4.plot([], [], color='red', label='Original')
line4_lin, = ax4.plot([], [], color='blue', label='Linear Scale')
line4_log, = ax4.plot([], [], color='green', label='Log Scale')

# Set titles
ax1.set_title('Original')
ax2.set_title('Linear Scale')
ax3.set_title('Log Scale')
ax4.set_title('All Lines Combined')

# Set axis limits for all subplots
for ax in [ax1, ax2, ax3, ax4]:
    ax.set_xlim(0, 2.41)
dataMax = max([max(d) for d in data])
dataMin = min([min(d) for d in data])
dataLinMax = max([max(d) for d in dataLinScale])
dataLinMin = min([min(d) for d in dataLinScale])
dataLogMax = max([max(d) for d in dataLogScale])
dataLogMin = min([min(d) for d in dataLogScale])
ax1.set_ylim(dataMin, dataMax)
ax2.set_ylim(dataLinMin, dataLinMax)
ax3.set_ylim(dataLogMin, dataLogMax)
ax4.set_ylim(min([dataMin,dataLogMin,dataLinMin]), max([dataMax,dataLogMax,dataLinMax]))

for ax in [ax1, ax2, ax3, ax4]:
    ax.xaxis.set_major_locator(MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(MultipleLocator(0.1))
    ax.grid(True, which='major', axis='x', linewidth=1)
    ax.grid(True, which='minor', axis='x', linestyle=':', alpha=0.4)

# Initialization function
def init():
    line1.set_data([], [])
    line2.set_data([], [])
    line3.set_data([], [])
    line4_orig.set_data([], [])
    line4_lin.set_data([], [])
    line4_log.set_data([], [])
    return line1, line2, line3, line4_orig, line4_lin, line4_log

def animate(i):
    x = np.linspace(0, 2.41, len(data[i]))
    linScale = [val for val in dataLinScale[i]]
    logScale = [val for val in dataLogScale[i]]
    y = [val for val in data[i]]
    
    # Update individual subplot lines
    line1.set_data(x, y)
    line2.set_data(x, linScale)
    line3.set_data(x, logScale)
    
    # Update combined subplot lines
    line4_orig.set_data(x, y)
    line4_lin.set_data(x, linScale)
    line4_log.set_data(x, logScale)
    
    return line1, line2, line3, line4_orig, line4_lin, line4_log

plt.tight_layout()
anim = animation.FuncAnimation(fig, animate, init_func=init,
                              frames=len(data), interval=100, blit=True)
plt.show()