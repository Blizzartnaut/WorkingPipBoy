import sys
import serial
import platform
import os
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import QTimer, QDate, QTime, QIODevice
from PySide6.QtGui import QPixmap
from PipBoyMenu import Ui_MainWindow #Importing UI elements from the UI file
from PIL import Image
from osgeo import gdal
import pynmea2

dir_path = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.data_sens1 = np.zeros(720) #Data for sensor 1
        self.data_sens2 = np.zeros(720)
        self.data_sens3 = np.zeros(720)

        os_name = platform.system() #Detects current system

        # self.data = np.zeros(720)  #Collects 1440 data points for 24 hours

        if os_name == "Windows":
            self.serial_port = serial.Serial('COM3', baudrate=19200, timeout=1) #For testing
        elif os_name == "Linux":
            self.serial_port = serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=1) #For the Raspberry Pi
            serial_port = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

            while True:
                #Read data from serial port
                line = serial_port.readline().decode('ascii', errors='replace')

                #Parse nmea sentance
                if line.startswith('$GPGGA'):
                    msg = pynmea2.parse(line)
                    print(f"Latitude: {msg.latitude}, Longitude: {msg.longitude}")
        else:
            raise Exception("Unsupported Operating System")
        
        self.map_timer = QTimer(self)
        self.map_timer.timeout.connect(self.update_map)
        self.map_timer.start(5000) #Updates map every minute
        
        self.graph_timer = QTimer(self)
        self.graph_timer.timeout.connect(self.update_graph)
        self.graph_timer.start(10000) #Updates graph every minute

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.read_Serial)    #Reads the serial every 100 ms
        self.time_timer.start(100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)         #Updates time and date every second
        self.timer.start(1000)

    def update(self):
        #Example: Update a QLabel with current date and time
        self.DATE.setText("Date: " + QDate().currentDate().toString())  #Sets Date Label to this text
        self.TIME.setText("Time: " + QTime().currentTime().toString())

    def read_Serial(self):
        if self.serial_port.in_waiting > 0:
            #Read Data from Serial Port
            data = self.serial_port.readline().decode('utf-8').strip() #Gets rid of both before and after
            values = data.split(',') #CSV

            self.data_sens1 = np.roll(self.data_sens1, -1)
            self.data_sens2 = np.roll(self.data_sens2, -1)
            self.data_sens3 = np.roll(self.data_sens3, -1)
            # self.data[-1] = float(values[0])

            #Uodate with latest sensor values
            self.data_sens1[-1] = float(values[0]) #Sensor 1 (MQ4)
            self.data_sens2[-1] = float(values[1]) #Sensor 2 (MQ6)
            self.data_sens3[-1] = float(values[2]) #Sensor 3 (MQ135)

            #Update UI with recieved data
            if len(values) >= 5:
                self.SENS1.setText(f"MQ4: {values[0]}") #Sets sens1 label to this value
                self.SENS2.setText(f"MQ6: {values[1]}")
                self.SENS3.setText(f"MQ135: {values[2]}")
                self.sel_4.setText(f"RAD: {values[3]}")
                menuScreen = values[4]

            self.update_graph()

    def update_graph(self):
        #Creates new figure and axis
        fig, ax = plt.subplots()

        #Plot the data
        ax.plot(self.data_sens1, color="blue", label="MQ4")
        ax.plot(self.data_sens2, color="red", label="MQ6")
        ax.plot(self.data_sens3, color="green", label="MQ135")

        #Set Labales and title
        ax.set_title('Past 24 Hours')
        ax.set_xlabel('Time (min)')
        ax.set_ylabel('Value')

        #add legend
        ax.set_xlim(len(self.data_sens1) - 300, len(self.data_sens1))
        ax.legend()

        #Save as BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        #Load image into QPixmap and display it on QLabel
        # self.graph_pixmap = QPixmap()
        # self.graph_pixmap.loadFromData(buf.getvalue())
        # self.SENSGRAPH.setPixmap(self.graph_pixmap)
        qimage = QPixmap()
        qimage.loadFromData(buf.getvalue())
        self.SENSGRAPH.setPixmap(qimage)

        #Close figure to free memory
        plt.close(fig)

    def update_map(self):
        #Create folium map on current coordinates
        lat, lon = self.get_current_gps_coordinates()
        # m = folium.Map(location=[lat,lon], zoom_start=14)
        zoom = 14

        #Add Marker
        #Get Paths to the relevant tiles
        tile_paths = self.get_tile_paths(zoom, lat, lon)

        #Create GDAL VRT (virtual raster) to stitch tiles together
        vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic', addAlpha=True)
        vrt = gdal.BuildVRT('/vsimem/stitched.vrt', tile_paths, options=vrt_options)

        #Convert VRT to PNG
        gdal.Translate('stitched_map.png', vrt, format='PNG')

        #Convert 2 QPixmap and display it on the label
        self.MAP.setPixmap(QPixmap('stitched_map.png'))

    def get_current_gps_coordinates(self):
        return 40.7128, -74.0060
    
    def get_tile_paths(self, zoom, lat, lon):
        #calculate x and y tile coordinates
        x = int((lon + 180.0) / 360.0 * (2.0 ** zoom))
        y = int((1.0 - (lat + 90) / 180.0) * (2.0 ** zoom))

        #Return paths to four tiles around coordinates
        tile_coords = [(x,y),(x + 1,y), (x,y+1),(x+1,y+1)]
        tile_paths = [f"tiles/{zoom}/{coord[0]}/{coord[1]}.png" for coord in tile_coords]
        return tile_paths
    
    # def read_gps_data():
        #open serial port
        # serial_port = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

        # while True:
        #     #Read data from serial port
        #     line = serial_port.readline().decode('ascii', errors='replace')

        #     #Parse nmea sentance
        #     if line.startswith('$GPGGA'):
        #         msg = pynmea2.parse(line)
        #         print(f"Latitude: {msg.latitude}, Longitude: {msg.longitude}")
    #             return msg.latitude, msg.longitude
            
    # def print_gps():
    #     latitude, longitude = read_gps_data()
    #     print(f"Current location: Latitude = {latitude}, Longitude = {longitude}")
    

app = QApplication([])
window = MainWindow()
window.show()
sys.exit(app.exec())