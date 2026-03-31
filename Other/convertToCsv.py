import pickle
import numpy as np
import math
import csv


folder = 'Pipe_241_3/'

data = []
dataLin = []
dataLog = []
x = np.linspace(0, 2.41, 64)


csvLinFile = open(f"Datasets/{folder[0:-1]}_Lin.csv","w",newline="")
csvLogFile = open(f"Datasets/{folder[0:-1]}_Log.csv","w",newline="")
    
writerLin = csv.writer(csvLinFile)
writerLog = csv.writer(csvLogFile)
writerLin.writerow(["Position"] + list(x))
writerLog.writerow(["Position"] + list(x))

with open(folder + 'None.pkl', 'rb') as f:
    fileData = pickle.load(f)

fileData = [val[8] for val in fileData]
for i in range(len(fileData)):
    dataLin.append([(32.0/float(len(x))) * (2**(val/512.0)) for val in fileData[i]])
    dataLog.append([(val*20.0*math.log10(2.0))/512.0 + 20.0*math.log10(32.0/float(len(x))) for val in fileData[i]])
    
for val in dataLin:
    writerLin.writerow(["None"] + list(val))
for val in dataLog:
    writerLog.writerow(["None"] + list(val))

for i in range(5,205,5):
    with open(folder + f'{i}.pkl', 'rb') as f:
        fileData = pickle.load(f)
    fileData = [val[8] for val in fileData]

    dataLin = []
    dataLog = []
    for j in range(len(fileData)):
        dataLin.append([(32.0/float(len(x))) * (2**(val/512.0)) for val in fileData[j]])
        dataLog.append([(val*20.0*math.log10(2.0))/512.0 + 20.0*math.log10(32.0/float(len(x))) for val in fileData[j]])

    for val in dataLin:
        writerLin.writerow([f"{i}"] + list(val))
    for val in dataLog:
        writerLog.writerow([f"{i}"] + list(val))


csvLinFile.close()
csvLogFile.close()