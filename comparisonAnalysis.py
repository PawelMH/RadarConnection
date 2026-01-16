import pickle
from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np



with open('savedData50cm.pkl', 'rb') as f:
    data = pickle.load(f)

# Create figure and axis
fig, ax = plt.subplots()

# Initialize the line with first frame data
line, = ax.plot([], [],color='red')

# Set axis limits based on data
#ax.set_xlim(0, len(data[0][8]))
#ax.set_ylim(min([min(d[8]) for d in data]), max([max(d[8]) for d in data]))

ax.set_xlim(0, 2.41)
y_scale = 89.0
ax.set_ylim(min([min(d[8]) for d in data]) / y_scale, max([max(d[8]) for d in data]) / y_scale)

# Initialization function
def init():
    line.set_data([], [])
    return line,

# Animation function (i is the frame number)
def animate(i):
    #x = range(len(data[i][8]))
    #y = data[i][8]
    x = np.linspace(0, 2.41, len(data[i][8]))
    y = [val / y_scale for val in data[i][8]]
    line.set_data(x, y)
    ax.set_title(f'Frame {i}')
    return line,

# Create animation
anim = animation.FuncAnimation(fig, animate, init_func=init,
                              frames=len(data), interval=100, blit=True)

plt.show()