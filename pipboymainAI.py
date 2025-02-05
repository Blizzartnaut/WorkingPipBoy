#activate the virtual environment
# if self.os_name == "Windows":
#     pass
# elif self.os_name == "Linux":
#     try:
#         source /home/marceversole/WorkingPipBoy/PipBoyVenv/bin/activate
#     except Exception as e:
#         print("Error loading venv")

import sys
import serial
import platform
import os
import numpy as np
import matplotlib.pyplot as plt
import math
from io import BytesIO

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
try:
    from osgeo import gdal
except ImportError:
    gdal = None

#for HTML Serving
import threading
import http.server
import socketserver

#Battery Status
# try:
#     from pijuice import PiJuice
# except ImportError:
#     pijuice = None

#Import UPSPro stuff
try:
    import time
    import smbus2
    import logging
    from ina219 import INA219, DeviceRangeError
except ImportError:
    time = None
    smbus2 = None
    logging = None
    ina219 = None

#Will do at a later time, need to make the fuel gage and plug it into the program
# DEVICE_BUS = 1
# DEVICE_ADDR = 0x17


# Dangerous do not use
# os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--allow-file-access-from-files"

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

        from PySide6.QtWidgets import QVBoxLayout, QWidget
        
        # Initialize sensor data arrays (720 data points per sensor)
        self.data_sens1 = np.zeros(720)  # Sensor 1 (e.g., MQ4)
        self.data_sens2 = np.zeros(720)  # Sensor 2 (e.g., MQ6)
        self.data_sens3 = np.zeros(720)  # Sensor 3 (e.g., MQ135)
        
        # Track the current menu screen as an instance attribute
        self.menuScreen = 1

        #Map placement
        server = start_local_server(port=8000, directory=".")
        
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
        # self.graph_timer.start(5000)
        
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
        self.memory_timer.timeout.connect(self.update)
        self.memory_timer.start(5000)
        
        #Matplotlib persistant canvas
        self.graphWidget = self.findChild(QWidget, "SENSGRAPH")
        if self.graphWidget is None:
            self.graph_timer.start(5000)
        
        graph_layout = QVBoxLayout(self.graphWidget)
        self.graphWidget.setLayout(graph_layout)

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
            
        # # # Look for a placeholder widget named "MAP" in your UI.
        # self.MAP = self.findChild(QWidget, "MAP")
        # if self.MAP is None:
        #     # If your UI does not already have one, create a placeholder.
        #     self.MAP = QWidget(self)
        #     self.MAP.setGeometry(174, 19, 611, 401)
        #     self.tabWidget.addTab(self.MAP, "Map")  # Optionally, add it to your tab widget.

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
            # #Plot the data
            # ax.plot(self.data_sens1, color="blue", label="MQ4")
            # ax.plot(self.data_sens2, color="red", label="MQ6")
            # ax.plot(self.data_sens3, color="green", label="MQ135")
            
            # #Set Labales and title
            # ax.set_title('Past 5 Minutes')
            # ax.set_xlabel('Time (sec)')
            # ax.set_ylabel('Value')
            # #add legend
            ax.set_xlim(max(0, len(self.data_sens1) - 300), len(self.data_sens1))
            # ax.legend()
            
            self.line1.set_ydata(self.data_sens1)            
            self.line2.set_ydata(self.data_sens2)            
            self.line3.set_ydata(self.data_sens3)

            self.canvas.draw_idle()
        except Exception as e:
            print("Error Updating Graph", e)
        #     #Save as BytesIO object
        #     buf = BytesIO()
        #     plt.savefig(buf, format="png")
        #     buf.seek(0)
            
        #     #Load image into QPixmap and display it on QLabel
        #     graph_pixmap = QPixmap()
        #     # Convert buffer data to bytes for PySide6 compatibility.
        #     graph_pixmap.loadFromData(bytes(buf.getvalue()))
        #     self.SENSGRAPH.setPixmap(graph_pixmap)
        #     self.SENSGRAPH.setScaledContents(True)
        # except Exception as e:
        #     print("Error updating graph:", e)
        # finally:
        #     plt.close(fig)  # Close the figure to prevent memory leaks.
    
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
        # For demonstration, we simulate GPS data. Replace this with your actual GPS retrieval.
        # For example, you might call self.read_gps_data() if that method is properly implemented.
        lat, lon = self.get_current_gps_coordinates()  # Replace with real GPS data when available
        
        # Build the JavaScript call to update the marker on the map.
        js_code = f"updateMarker({lat}, {lon});"
        # Run the JavaScript in the QWebEngineView.
        self.mapView.page().runJavaScript(js_code)
        print(f"Updated GPS marker to lat: {lat}, lon: {lon}")
    
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
            print('GPS data not found')
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
            print("GPS serial port not initialized.")
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
        print(f"Memory Usage: {percent_usage:.1f}% ({used_mb:.1f} MB used out of 1840 MB)")

        # Update the progress bar
        # Option 1: If your progress bar's range is 0-100, set the value to the percentage:
        self.progressBar_2.setValue(int(percent_usage))

        # Option 2: If you want the progress bar to show MB directly, first set its maximum to 1840:
        # self.progressBar_2.setMaximum(1840)
        # self.progressBar_2.setValue(int(used_mb))
    
    # def get_battery_status():
    #     try:
    #         pj = PiJuice(1, 0x14) #Adjust I2C bus and address as needed
    #         status = pj.GetBatteryStatus()
    #         #
        
if __name__ == "__main__":
    # Use sys.argv for proper argument parsing in PySide6
    app = QApplication(sys.argv)
    window = MainWindow()
    window.start_fullscreen()
    sys.exit(app.exec())