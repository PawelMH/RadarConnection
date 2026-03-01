import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget,
                             QHBoxLayout,QVBoxLayout,QTextEdit,QPushButton,
                             QTabWidget, QSlider, QLineEdit)
from PyQt6.QtCore import Qt
import pyqtgraph.opengl as gl
import pyqtgraph as pg

from radar import Radar
import threading
import time
import pickle
import numpy as np

class RadarGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IWR1443 Radar Tester")
        self.setGeometry(100,100,800,600)
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QHBoxLayout(self.centralWidget)
        
        self.renderedSpheres = []

        self.columnSettings = self.create_column_settings()
        self.columnViewport = self.create_column_viewport()
        self.columnCommands = self.create_column_commands()
        
        self.mainLayout.addWidget(self.columnSettings)
        self.mainLayout.addWidget(self.columnViewport)
        self.mainLayout.addWidget(self.columnCommands)

        self.mainLayout.setStretch(0,1)
        self.mainLayout.setStretch(1,2)
        self.mainLayout.setStretch(2,1)

        self.apply_styles()

        self.fps = 5.0
        self.radar = Radar("COM7","COM6")

    def create_column_settings(self):
        column = QWidget()
        column.setObjectName("column-settings")
        layout = QVBoxLayout(column)

        uploadButton = QPushButton("Upload Configuration")
        uploadButton.clicked.connect(self.upload_commands)
        layout.addWidget(uploadButton)

        stopButton = QPushButton("Stop Radar")
        stopButton.clicked.connect(self.stop_radar)
        layout.addWidget(stopButton)

        recordLayout = QHBoxLayout()

        self.recordFilenameEdit = QLineEdit()
        self.recordFilenameEdit.setPlaceholderText("filename")
        self.recordFilenameEdit.setText("recording_01")

        self.recordButton = QPushButton("Record Data")
        self.recordButton.setCheckable(True)
        self.recordButton.clicked.connect(self.toggle_record)

        recordLayout.addWidget(self.recordButton)
        recordLayout.addWidget(self.recordFilenameEdit)

        layout.addLayout(recordLayout)


        return column
    
    def toggle_record(self, checked):

        if checked:
            filename = self.recordFilenameEdit.text().strip()

            if not filename:
                print("Please enter a filename")
                self.recordButton.setChecked(False)
                return
            self.filename = filename

            self.recordButton.setText("Stop Recording")

            if len(self.radar.storedData):
                self.recordStart = len(self.radar.storedData) - 1
            else:
                self.recordStart = 0

        else:
            self.recordButton.setText("Record Data")
            
            with open(f"{self.filename}.pkl", 'wb') as f:
                pickle.dump(self.radar.storedData[self.recordStart:len(self.radar.storedData)], f)



    def upload_commands(self):
        for cmd in self.commandsText.toPlainText().split('\n'):
            self.radar.send_cmd(cmd)
        
        self.radar.active = True
        self.radar.storedData = []

        # Create and start the thread
        self.radarThread = threading.Thread(target=self.radar.run)
        self.radarThread.start()

        self.viewportThread = threading.Thread(target=self.update_viewport_radar)
        self.viewportThread.start()

    def update_viewport_radar(self):
        
        denoise = False
        frameIdx = 0

        while (self.radar.active and len(self.radar.storedData) == 0):
            pass

        while self.radar.active:
                if len(self.radar.storedData) > frameIdx:
                    frameIdx =  len(self.radar.storedData)
                else:
                    time.sleep(0.02)
                    continue
                print(f"Frame Number: {len(self.radar.storedData)}")
                if self.radar.storedData[-1][7] == None:
                    points = None
                else:
                    points = [sublist[0] for sublist in self.radar.storedData[-1][7]]
                self.update_viewport(points=points, threshold=self.peakThreshold)

                #if len(self.radar.storedData) > 50 and denoise == False:
                #    denoise = False
                #    self.calc_noise_profile()

                self.update_range_view(points=self.radar.storedData[-1][8], denoise=denoise)

    def stop_radar(self):
        self.radar.active = False
        # Wait for the radar thread to finish
        if hasattr(self, 'radarThread') and self.radarThread.is_alive():
            self.radarThread.join()
        if hasattr(self, 'viewportThread') and self.viewportThread.is_alive():
            self.viewportThread.join()



    def create_column_viewport(self):
        column = QWidget()
        column.setObjectName("column-viewport")
        layout = QVBoxLayout(column)

        # Create tab widget
        self.tabWidget = QTabWidget()
        #################################################################################
        # Create 2D view tab
        tab2D = QWidget()
        layout2D = QVBoxLayout(tab2D)

        self.plot2D = pg.PlotWidget()
        self.plot2D.setMinimumSize(400, 400)
        self.plot2D.setLabel('left', 'Y Position')
        self.plot2D.setLabel('bottom', 'X Position')
        self.plot2D.setTitle('2D Top-Down View (X-Y)')
        self.plot2D.showGrid(x=True, y=True)
        self.plot2D.setAspectLocked(True)  # Keep aspect ratio square

        self.plot2D.setXRange(-4, 4, padding=0)
        self.plot2D.setYRange(-1, 10, padding=0)
        self.plot2D.disableAutoRange()  # Disable auto-ranging

        # Create scatter plot item
        self.scatter2D = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 200))
        self.plot2D.addItem(self.scatter2D)

        layout2D.addWidget(self.plot2D)

        #################################################################################
        # Create range viewer tab

        tabRange = QWidget()
        layoutRange = QVBoxLayout(tabRange)

        self.plotRange = pg.PlotWidget()
        self.plotRange.setMinimumSize(400, 400)
        self.plotRange.setLabel('left', 'Gain (dB)')
        self.plotRange.setLabel('bottom', 'Range (M)')
        self.plotRange.setTitle('Range - Gain')
        self.plotRange.showGrid(x=True, y=True)

        self.plotRange.setXRange(0,9.29)
        self.plotRange.setYRange(0,10000)
        self.plotRange.disableAutoRange()  # Disable auto-ranging

        # Create scatter plot item
        self.scatterRange = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 200))
        self.plotRange.addItem(self.scatterRange)

        layoutRange.addWidget(self.plotRange)

        #################################################################################
        # Add tabs to tab widget
        self.tabWidget.addTab(tabRange, "Range View")
        self.tabWidget.addTab(tab2D, "2D View (X-Y)")
        

        layout.addWidget(self.tabWidget)

        # Add threshold slider below tabs
        sliderWidget = QWidget()
        sliderLayout = QHBoxLayout(sliderWidget)

        sliderLabel = QLabel("Peak Threshold:")
        sliderLayout.addWidget(sliderLabel)

        self.thresholdSlider = QSlider(Qt.Orientation.Horizontal)
        self.thresholdSlider.setMinimum(0)
        self.thresholdSlider.setMaximum(100)
        self.peakThreshold = 30
        self.thresholdSlider.setValue(self.peakThreshold)  # Default value
        self.thresholdSlider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.thresholdSlider.setTickInterval(10)
        self.thresholdSlider.valueChanged.connect(self.on_threshold_changed)
        sliderLayout.addWidget(self.thresholdSlider)

        self.thresholdValueLabel = QLabel("30")
        self.thresholdValueLabel.setMinimumWidth(30)
        sliderLayout.addWidget(self.thresholdValueLabel)

        layout.addWidget(sliderWidget)

        return column

    def on_threshold_changed(self, value):
        self.peakThreshold = value
        self.thresholdValueLabel.setText(str(value))

    def update_range_view(self, points, denoise = False):
        x = np.linspace(0, 9.29, len(points))
        if denoise:
            self.scatterRange.setData(x,self.denoise_range(points))
        else:
            self.scatterRange.setData(x,points)

    def update_viewport(self, points, threshold=30):
        if points == None:
            #Clear 2D view
            self.scatter2D.setData([], [])
            return

        scaleFactor = 1.0

        #Lists for 2D plotting
        x_coords = []
        y_coords = []

        for coord in points:
            if coord[2] < threshold:
                continue

            #Collect coordinates for 2D plot
            x_coords.append(coord[3] * scaleFactor)
            y_coords.append(coord[4] * scaleFactor)

        # Update 2D scatter plot
        self.scatter2D.setData(x_coords, y_coords)

    def create_column_commands(self):
        column = QWidget()
        column.setObjectName("column-settings")
        layout = QVBoxLayout(column)

        title = QLabel("Current Configuration:")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.commandsText = QTextEdit()
        self.commandsText.setReadOnly(True)
        self.commandsText.setObjectName("commands-display")

        sample_commands = """sensorStop
flushCfg
dfeDataOutputMode 1
channelCfg 15 5 0
adcCfg 2 1
adcbufCfg 0 1 0 1
profileCfg 0 77 372 7 114.29 0 0 35 1 224 2107 0 0 30
chirpCfg 0 0 0 0 0 0 0 1
chirpCfg 1 1 0 0 0 0 0 4
frameCfg 0 1 16 0 100 1 0
lowPower 0 1
guiMonitor 1 1 0 0 0 0
cfarCfg 0 2 8 4 3 0 1280
peakGrouping 1 1 1 1 229
multiObjBeamForming 1 0.5
clutterRemoval 0
calibDcRangeSig 0 -5 8 256
compRangeBiasAndRxChanPhase 0.0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0
measureRangeBiasAndRxChanPhase 0 1.5 0.2
CQRxSatMonitor 0 3 11 121 0
CQSigImgMonitor 0 111 4
analogMonitor 1 1"""
        
        self.commandsText.setPlainText(sample_commands)
        layout.addWidget(self.commandsText)
        
        # Save button
        self.saveButton = QPushButton("Save Configuration")
        #self.saveButton.clicked.connect(self.save_configuration)
        layout.addWidget(self.saveButton)
        
        # Load button
        self.loadButton = QPushButton("Load Configuration")
        #self.loadButton.clicked.connect(self.load_configuration)
        layout.addWidget(self.loadButton)

        return column

    def apply_styles(self):
        """Load and apply CSS stylesheet from external file"""
        try:
            with open('style.css', 'r') as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print("Warning: style.css not found. Using default styles.")
            # Fallback to default styles if file doesn't exist
            self.setStyleSheet("")

    def calc_noise_profile(self):
        noiseProfile = []
        for i in range(len(self.radar.storedData[0][8])):
            temp = 0
            for j in range(30):
                temp += self.radar.storedData[j][8][i]
            temp /= 40.0
            noiseProfile.append(temp)

        self.noiseProfile = noiseProfile

    def denoise_range(self, points):
        #Take average amplitudes and subtract them from the current range.
        return [points[i] - self.noiseProfile[i] for i in range(len(points))]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RadarGUI()
    window.show()
    sys.exit(app.exec())