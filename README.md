# Radar Sensing in Pipes
## File Structure
There are 3 main python files which are:
### display.py
This is the GUI to communicate with the IWR1443Boost evaluation board, used to visualise and record data
### PeakAnalysis.ipynb
This is the Jupyter Notebook to analyse a single dataset
### MultiFilePeakAnalysis.py
This is a python file to plot multiple datasets on the same graph

## Datasets
- The datasets are stored inside the "Data" folder with each subfolder containing each individual measurement
- Filenames follow: `{Measurement Environment}_{Measurement Target}_{Max unambiguous range}`
- Range resolution depends on max unambiguous range:
  - 717 → 35.2 mm
  - 241 → 46.875 mm