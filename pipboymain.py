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
#from datetime import datetime
# from selenium import webdriver
# import webbrowser
from html2image import Html2Image
from PIL import Image
import folium

dir_path = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        os_name = platform.system() #Detects current system

        self.data = np.zeros(1440)  #Collects 1440 data points for 24 hours

        if os_name == "Windows":
            self.serial_port = serial.Serial('COM3', baudrate=19200, timeout=1) #For testing
        elif os_name == "Linux":
            self.serial_port = serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=1) #For the Raspberry Pi
        else:
            raise Exception("Unsupported Operating System")
        
        self.map_timer = QTimer(self)
        self.map_timer.timeout.connect(self.update_map)
        self.map_timer.start(5000) #Updates map every minute

        self.htm2img = Html2Image()
        self.htm2img.size = (581,531)

        # #Selenium webdriver setup for map render
        # options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  #Run headless (without GUI)
        # self.driver = webdriver.Chrome(options=options)
        
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

            self.data = np.roll(self.data, -1)
            self.data[-1] = float(values[0])

            #Update UI with recieved data
            if len(values) >= 5:
                self.SENS1.setText(f"MQ4: {values[0]}") #Sets sens1 label to this value
                self.SENS2.setText(f"MQ6: {values[1]}")
                self.SENS3.setText(f"MQ135: {values[2]}")
                self.sel_4.setText(f"RAD: {values[3]}")
                menuScreen = values[4]

    def update_graph(self):
        #Creates new figure and axis
        fig, ax = plt.subplots()

        #Plot the data
        ax.plot(self.data, color="blue")
        # ax.plot(self.data[1], color="red")
        # ax.plot(self.data[2], color="green")

        #Set Labales and title
        ax.set_title('Past 24 Hours')
        ax.set_xlabel('Time (min)')
        ax.set_ylabel('Value')

        #Save as BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        #Load image into QPixmap and display it on QLabel
        self.graph_pixmap = QPixmap()
        self.graph_pixmap.loadFromData(buf.getvalue())
        self.SENSGRAPH.setPixmap(self.graph_pixmap)

        #Close figure to free memory
        plt.close(fig)

    def update_map(self):
        #Create folium map on current coordinates
        lat, lon = self.get_current_gps_coordinates()
        m = folium.Map(location=[lat,lon], zoom_start=14)

        #Add Marker
        folium.Marker([lat,lon], tooltip="Current Location").add_to(m)

        #Save map as HTML file
        map_file = 'current_map.html'
        m.save(map_file)
        # webbrowser.open('current_map.html', new=2)

        #Render Map using selenium and grab the image
        # self.driver(f'file://{os.path.realpath(map_file)}')
        # png = self.driver.get_screenshot_as_png()
        self.htm2img.screenshot(html_file=map_file, save_as='map.png', size=(581,531))
        #is there a way to do this without a screenshot?

        #Convert 2 QPixmap and display it on the label
        # image = Image.open(BytesIO(png))
        # bufm = BytesIO()
        # image.save(bufm, format='PNG')
        # qimage = QPixmap()
        # qimage.loadFromData(bufm.getvalue())
        self.MAP.setPixmap(QPixmap('map.png'))

    def get_current_gps_coordinates(self):
        return 40.7128, -74.0060

app = QApplication([])
window = MainWindow()
window.show()
# app.exec()
sys.exit(app.exec())