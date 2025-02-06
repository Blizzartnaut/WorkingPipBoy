# import subprocess

# #setup venv
# def activate_venv():
#     subprocess.run(["source", "PipBoyVenv/bin/activate"])  # On Linux/Mac

# #Activate venv
# activate_venv()

import sys
import serial
import platform
import os
import numpy as np
import matplotlib.pyplot as plt
import math
from io import BytesIO
import gc

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import QTimer, QDate, QTime, QIODevice, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

# Import the UI file generated for PySide6 (ensure you ran pyside6-uic)
from PipBoyMenu import Ui_MainWindow

from PIL import Image
import pynmea2
import psutil #For monitoring memory

try:
    from matplotlib.backends.backend_qt6agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.figure import Figure

# Attempt to import GDAL if available; if not, set to None.
# try:
#     from osgeo import gdal
# except ImportError:
#     gdal = None

#for HTML Serving
import threading
import http.server
import socketserver

#Battery Status


#Import x728 stuff
import struct
import smbus
import time

def start_local_server(port=8000, directory="."):
    """
    Start an HTTP server serving files from the specified directory.
    The server runs in a background daemon thread.
    """
    # Save current working directory and change to the desired directory.
    cwd = os.getcwd()
    os.chdir(directory)
    
    handler = http.server.SimpleHTTPRequestHandler
    # Allow address reuse so that you can restart the server without waiting.
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", port), handler)
    
    # Start the server in a daemon thread (so it closes when your main app closes).
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    
    os.chdir(cwd)
    print(f"Local HTTP server started on port {port}, serving directory: {directory}")
    return httpd

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # Set up UI elements (ensure the .ui file has been updated for PySide6)
        self.setupUi(self)

        self.progressBar_2.setMinimum(0)
        self.progressBar_2.setMaximum(100)

        from PySide6.QtWidgets import QVBoxLayout, QWidget
        
        # Initialize sensor data arrays (720 data points per sensor)
        self.data_sens1 = np.zeros(720)  # Sensor 1 (e.g., MQ4)
        self.data_sens2 = np.zeros(720)  # Sensor 2 (e.g., MQ6)
        self.data_sens3 = np.zeros(720)  # Sensor 3 (e.g., MQ135)
        
        # Track the current menu screen as an instance attribute
        self.menuScreen = 1

        #Map placement
        server = start_local_server(port=8000, directory=".")

        #Bus for battery capacity gauge
        self.bus = smbus.SMBus(1) #0 = /dev/i2c-0 (port I@C0), 1 = /dev/i2c-1 (port I2C1)
        
        # Detect the operating system for conditional functionality
        self.os_name = platform.system()
        
        # Initialize serial ports based on platform:
        if self.os_name == "Windows":
            pass
        elif self.os_name == "Linux":
            try:
                self.serial_port = serial.Serial('/dev/ttyACM0', baudrate=19200, timeout=1)
            except Exception as e:
                print("Error initializing serial port on Linux:", e)
            try:
                self.serial_portGPS = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
            except Exception as e:
                print("Error initializing GPS serial port on Linux:", e)
        else:
            raise Exception("Unsupported Operating System")
        
        # Timers for various periodic updates:
        
        # Graph update timer: refresh graph every 10 seconds.
        self.graph_timer = QTimer(self)
        self.graph_timer.timeout.connect(self.update_graph)
        
        # Serial data reading timer: check for serial data every 100 ms.
        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self.read_Serial)
        self.serial_timer.start(100)
        
        # UI time/date update timer: update labels every second.
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update)
        self.datetime_timer.start(1000)

        #To update memory every 5 seconds
        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)

        # #Manual Triggering of Garbage Collection #did something weird, disabled for further investigation, suspect
        # self.gacl = QTimer(self)
        # self.gacl.timeout.connect(self.run_gc)
        # self.gacl.start(10000)
        
        #Matplotlib persistant canvas
        self.graphWidget = self.findChild(QWidget, "SENSGRAPH")
        if self.graphWidget is None:
            self.graph_timer.start(5000)
        
        graph_layout = QVBoxLayout(self.graphWidget)
        self.graphWidget.setLayout(graph_layout)
        self.graphWidget.setScaledContents(True)

        self.figure = Figure(figsize=(6,4))
        self.canvas = FigureCanvas(self.figure)
        graph_layout.addWidget(self.canvas)

        #Set Labales and title
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Past 5 Minutes')
        self.ax.set_xlabel('Time (sec)')
        self.ax.set_ylabel('Value')

        #Plot the data
        self.line1, = self.ax.plot(self.data_sens1, color="blue", label="MQ4")
        self.line2, = self.ax.plot(self.data_sens2, color="red", label="MQ6")
        self.line3, = self.ax.plot(self.data_sens3, color="green", label="MQ135")
            
        #add legend
        # self.ax.set_xlim(max(0, len(self.data_sens1) - 300), len(self.data_sens1))
        self.ax.legend()
        self.canvas.draw()

        # Create a vertical layout for the container if not already set.
        if self.MAP.layout() is None:
            layout = QVBoxLayout(self.MAP)
            self.MAP.setLayout(layout)
        else:
            layout = self.MAP.layout()
            
        # Create a layout for the container and add the QWebEngineView to it.
        # layout = QVBoxLayout(self.MAP)
        self.mapView = QWebEngineView()
        local_map_path = os.path.abspath("pipboy_map.html")
        self.mapView.load(QUrl("http://localhost:8000/pipboy_map.html"))
        layout.addWidget(self.mapView)
        
        # NEW: Timer to update GPS marker (calls update_gps_marker method)
        self.gps_timer = QTimer(self)
        self.gps_timer.timeout.connect(self.update_gps_marker)
        self.gps_timer.start(2000)  # Update every 2 seconds (adjust as needed)

        # Battery Capacity Update
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(10000)

    def start_fullscreen(self):
        self.showFullScreen()
    
    def update(self):
        """
        Update date and time labels on the UI.
        Ensure that the UI file defines labels with the object names 'DATE' and 'TIME';
        otherwise, update these names to match the UI.
        """
        self.DATE.setText("Date: " + QDate.currentDate().toString())
        self.TIME.setText("Time: " + QTime.currentTime().toString())
    
    def read_Serial(self):
        """
        Read incoming serial data if available. Expected CSV format:
        [value1, value2, value3, value4, menuScreen]
        Updates sensor arrays and UI labels.
        """
        if hasattr(self, 'serial_port') and self.serial_port.in_waiting > 0:
            try:
                data = self.serial_port.readline().decode('utf-8').strip()
                values = data.split(',')
                
                # Roll arrays to make room for new data at the end.
                self.data_sens1 = np.roll(self.data_sens1, -1)
                self.data_sens2 = np.roll(self.data_sens2, -1)
                self.data_sens3 = np.roll(self.data_sens3, -1)
                
                # Update sensor data (ensure values[0-2] are valid floats)
                self.data_sens1[-1] = float(values[0])
                self.data_sens2[-1] = float(values[1])
                self.data_sens3[-1] = float(values[2])
                
                # Update UI if sufficient values are provided
                if len(values) >= 5:
                    self.SENS1.setText(f"MQ4: {values[0]}")
                    self.SENS2.setText(f"MQ6: {values[1]}")
                    self.SENS3.setText(f"MQ135: {values[2]}")
                    self.sel_4.setText(f"RAD: {values[3]}")
                    # try:
                    #     self.menuScreen = int(values[4])
                    # except ValueError:
                    #     print("Invalid menuScreen value received:", values[4])
                    # self.update_tab()
                
                # Update the graph with the new data
                self.update_graph()
            except Exception as e:
                print("Error in read_Serial:", e)
        else:
            # No data available on the serial port.
            pass
    
    def update_graph(self):
        """
        Render a matplotlib graph of the sensor data and display it in the UI.
        The graph is saved to a BytesIO buffer, then loaded into a QPixmap.
        """
        fig, ax = plt.subplots()
        try:
            self.ax.set_ylim(0, 1000)
            self.line1.set_ydata(self.data_sens1)            
            self.line2.set_ydata(self.data_sens2)            
            self.line3.set_ydata(self.data_sens3)

            self.ax.set_xlim(max(0, len(self.data_sens1) - 300), len(self.data_sens1))

            self.canvas.draw_idle()
        except Exception as e:
            print("Error Updating Graph", e)
    
    def update_tab(self):
        """
        Update the tab widget based on the menuScreen value.
        Adjusts the tab index; ensure that the UI defines a QTabWidget with the object name 'tabWidget'.
        """
        try:
            tab_index = int(self.menuScreen) - 1
            if tab_index != self.tabWidget.currentIndex():
                self.tabWidget.setCurrentIndex(tab_index)
        except Exception as e:
            print("Error updating tab:", e)
    
    # ---------------------------------------------------------------------
    # NEW: GPS Marker Update Functionality
    def update_gps_marker(self):
        """
        This function should retrieve current GPS coordinates (via your existing GPS method
        or a simulation) and then update the marker on the Leaflet map via JavaScript.
        """
        lat, lon = self.get_current_gps_coordinates()  # Replace with real GPS data when available
        
        # Build the JavaScript call to update the marker on the map.
        js_code = f"updateMarker({lat}, {lon});"
        # Run the JavaScript in the QWebEngineView.
        self.mapView.page().runJavaScript(js_code)
        # print(f"Updated GPS marker to lat: {lat}, lon: {lon}")
    
    def get_current_gps_coordinates(self):
        """
        Return the current GPS coordinates as (latitude, longitude).
        This function calls read_gps_data() to obtain data from the GPS hat.
        If no valid data is received, it falls back to fixed demo coordinates.
        """
        coords = self.read_gps_data()
        if coords != (None, None):
            return coords
        else:
            # Fallback fixed coordinates (for testing or if GPS data is unavailable)
            # print('GPS data not found')
            return 41.0120, -76.8477
    # ---------------------------------------------------------------------
    
    def read_gps_data(self):
        """
        Attempt to read one line from the GPS serial port and parse it.
        Returns a tuple (latitude, longitude) if a valid GPGGA sentence is found.
        If no valid data is available, returns (None, None).
        """
        if hasattr(self, 'serial_portGPS'):
            try:
                # Check if data is available to prevent blocking
                if self.serial_portGPS.in_waiting > 0:
                    line = self.serial_portGPS.readline().decode('ascii', errors='replace').strip()
                    if line.startswith('$GPGGA'):
                        msg = pynmea2.parse(line)
                        return (msg.latitude, msg.longitude)
            except Exception as e:
                print("Error reading GPS data:", e)
            return (None, None)
        else:
            # print("GPS serial port not initialized.")
            return (None, None)
        
    def update_memory_usage(self):
        # """
        # Use psutil to get current memory usage and update the progress bar.
        # This example assumes that the total memory is 1840 MB.
        # """
        mem = psutil.virtual_memory()
        # Calculate used memory in MB
        used_mb = mem.used / (1024 * 1024)
        # Calculate percentage based on a maximum of 1840 MB
        percent_usage = (used_mb / 1840) * 100

        # Print memory usage for debugging (optional)
        # print(f"Memory Usage: {percent_usage:.1f}% ({used_mb:.1f} MB used out of 1840 MB)")

        if percent_usage >= 90:
            quit()

        # Update the progress bar
        # Progress bar's range is 0-100, set the value to the percentage:
        self.progressBar_2.setValue(int(percent_usage))

    def run_gc(self):
        gc.collect()

    def read_capacity(self):
        address = 0x36
        read = self.bus.read_word_data(address, 4)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        capacity = swapped/256
        return capacity
    
    def update_battery_status(self):
        capacity = self.read_capacity()
        print(f'Current Capacity = {capacity}')
        self.progressBar.setValue(int(capacity))
        
if __name__ == "__main__":
    # Use sys.argv for proper argument parsing in PySide6
    app = QApplication(sys.argv)
    window = MainWindow()
    window.start_fullscreen()
    sys.exit(app.exec())