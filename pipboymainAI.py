import sys
import serial
import platform
import os
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
import math
from io import BytesIO
import gc
from collections import deque

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QProgressBar, QGridLayout, QSlider, QLabel, QHBoxLayout, QPushButton, QComboBox, QRadioButton, QSizePolicy
from PySide6.QtCore import QTimer, QDate, QTime, QIODevice, QUrl, Signal, QSize, Qt, QThread, QObject
from PySide6.QtGui import QPixmap, QMovie, QImage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

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

#for HTML Serving
import threading
import http.server
import socketserver

#Import x728 stuff
import struct
import smbus
import time

#Import GPS Mapping Functions
from gps_lib import GGA_Read, RMC_Read, GSV_Read

#for testing
radioval = 0

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

# Defaults
fft_size = 4096            # Size of the FFT to compute the spectrum (buffer size)
num_rows = 200             # Number of rows for the waterfall plot (each row represents one FFT result)
center_freq = 750e6        # Default center frequency (750 MHz)
sample_rates = [56, 40, 20, 10, 5, 2, 1, 0.5]  # Available sample rates in MHz
sample_rate = sample_rates[0] * 1e6  # Default sample rate in Hz (56 MHz)
time_plot_samples = 500    # Number of samples to show in the time-domain plot
gain = 50                  # Default gain (in dB)
sdr_type = "sim"           # The type of SDR to use ("sim" means simulated data; could also be "usrp" or "pluto")

# Init SDR
if sdr_type == "pluto":
    import adi
    sdr = adi.Pluto("ip:192.168.1.10")
    sdr.rx_lo = int(center_freq)
    sdr.sample_rate = int(sample_rate)
    sdr.rx_rf_bandwidth = int(sample_rate*0.8) # antialiasing filter bandwidth
    sdr.rx_buffer_size = int(fft_size)
    sdr.gain_control_mode_chan0 = 'manual'
    sdr.rx_hardwaregain_chan0 = gain # dB
elif sdr_type == "usrp":
    import uhd
    #usrp = uhd.usrp.MultiUSRP(args="addr=192.168.1.10")
    usrp = uhd.usrp.MultiUSRP(args="addr=192.168.1.201")
    usrp.set_rx_rate(sample_rate, 0)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), 0)
    usrp.set_rx_gain(gain, 0)

    # Set up the stream and receive buffer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = [0]
    metadata = uhd.types.RXMetadata()
    streamer = usrp.get_rx_stream(st_args)
    recv_buffer = np.zeros((1, fft_size), dtype=np.complex64)

    # Start Stream
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    def flush_buffer():
        for _ in range(10):
            streamer.recv(recv_buffer, metadata)


class SDRWorker(QObject):
    def __init__(self):
        super().__init__()
        self.gain = gain
        self.sample_rate = sample_rate
        self.freq = 0  # Frequency in kHz (to accommodate QSlider limits)
        self.spectrogram = -50 * np.ones((fft_size, num_rows))  # Initialize waterfall (spectrogram) matrix
        self.PSD_avg = -50 * np.ones(fft_size)  # Initialize an averaged power spectral density array

    # PyQt Signals – these are custom signals that will be emitted when new data is ready.
    time_plot_update = Signal(np.ndarray)
    freq_plot_update = Signal(np.ndarray)
    waterfall_plot_update = Signal(np.ndarray)
    end_of_run = Signal()  # Emitted each loop to signal that the worker is ready to run again

    # Slot functions to update frequency, gain, and sample rate
    def update_freq(self, val):
        print("Updated freq to:", val, 'kHz')
        if sdr_type == "pluto":
            sdr.rx_lo = int(val * 1e3)
        elif sdr_type == "usrp":
            usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(val * 1e3), 0)
            flush_buffer()

    def update_gain(self, val):
        print("Updated gain to:", val, 'dB')
        self.gain = val
        if sdr_type == "pluto":
            sdr.rx_hardwaregain_chan0 = val
        elif sdr_type == "usrp":
            usrp.set_rx_gain(val, 0)
            flush_buffer()

    def update_sample_rate(self, val):
        print("Updated sample rate to:", sample_rates[val], 'MHz')
        if sdr_type == "pluto":
            sdr.sample_rate = int(sample_rates[val] * 1e6)
            sdr.rx_rf_bandwidth = int(sample_rates[val] * 1e6 * 0.8)
        elif sdr_type == "usrp":
            usrp.set_rx_rate(sample_rates[val] * 1e6, 0)
            flush_buffer()

    # Main processing loop – this function is called repeatedly on a separate thread.
    def run(self):
        start_t = time.time()

        # Get samples from the chosen SDR source:
        if sdr_type == "pluto":
            samples = sdr.rx() / 2**11  # Scale received samples
        elif sdr_type == "usrp":
            streamer.recv(recv_buffer, metadata)
            samples = recv_buffer[0]
        elif sdr_type == "sim":
            # Generate simulated data (tone + noise)
            tone = np.exp(2j * np.pi * self.sample_rate * 0.1 * np.arange(fft_size) / self.sample_rate)
            noise = np.random.randn(fft_size) + 1j * np.random.randn(fft_size)
            samples = self.gain * tone * 0.02 + 0.1 * noise
            np.clip(samples.real, -1, 1, out=samples.real)
            np.clip(samples.imag, -1, 1, out=samples.imag)

        # Emit a signal for the time-domain plot (first time_plot_samples of the data)
        self.time_plot_update.emit(samples[0:time_plot_samples])

        # Compute the FFT to get the power spectral density (PSD)
        PSD = 10.0 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples)))**2 / fft_size)
        # Smooth (average) the PSD over time
        self.PSD_avg = self.PSD_avg * 0.99 + PSD * 0.01
        self.freq_plot_update.emit(self.PSD_avg)

        # Update the waterfall (spectrogram): roll the spectrogram matrix and add new FFT results
        self.spectrogram[:] = np.roll(self.spectrogram, 1, axis=1)
        self.spectrogram[:, 0] = PSD
        self.waterfall_plot_update.emit(self.spectrogram)

        #print("Frames per second:", 1 / (time.time() - start_t))
        self.end_of_run.emit()  # Signal that one processing loop is done

class SplashScreen(QMainWindow):
    def __init__(self, gif_path, audio_path, duration=3400):
        super().__init__()
        # Remove window borders and go full-screen
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        
        # Create a central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a label to hold the GIF
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Load and start the GIF using QMovie
        self.movie = QMovie(gif_path)
        self.label.setMovie(self.movie)
        self.movie.start()
        
        # Set up the audio player
        self.audio_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_player.setAudioOutput(self.audio_output)
        self.audio_player.setSource(QUrl.fromLocalFile(os.path.abspath(audio_path)))
        self.audio_output.setVolume(0.5)  # Adjust volume as needed
        self.audio_player.play()
        
        # Close the splash screen after the specified duration (milliseconds)
        QTimer.singleShot(duration, self.close)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # Set up UI elements (ensure the .ui file has been updated for PySide6)
        self.setupUi(self)

        self.progressBar_2.setMinimum(0)
        self.progressBar_2.setMaximum(100)

        # from PySide6.QtWidgets import QVBoxLayout, QWidget
        #Init SDR worker and thread
        self.sdr_thread = QThread()
        self.sdr_thread.setObjectName('SDR_Thread')
        worker = SDRWorker()
        worker.moveToThread(self.sdr_thread)

        #Create lineEdit to type in frequency for testing until we can implement additional hardware
        # self.freq_plot_butt.clicked.connect(self.display_freqplot)
        # self.time_plot_butt.clicked.connect(self.display_timeplot)
        # self.waterfall_butt.clicked.connect(self.display_colorbar)

        #Handle return pressed for frequency select
        # self.freqInput.returnPressed.connect(self.handle_freq_input)
        # self.freqInput.
        self.freq_val = 750.00 #Comment out when no longer testing

        # Signals and slots connections:
        def time_plot_callback(samples):
            time_plot_curve_i.setData(samples.real)
            time_plot_curve_q.setData(samples.imag)

        def freq_plot_callback(PSD_avg):
            # TODO figure out if there's a way to just change the visual ticks instead of the actual x vals
            f = np.linspace(self.freq_val*1e3 - worker.sample_rate/2.0, self.freq_val*1e3 + worker.sample_rate/2.0, fft_size) / 1e6
            freq_plot_curve.setData(f, PSD_avg)
            freq_plot.setXRange(self.freq_val*1e3/1e6 - worker.sample_rate/2e6, self.freq_val*1e3/1e6 + worker.sample_rate/2e6)

        def waterfall_plot_callback(spectrogram):
            imageitem.setImage(spectrogram, autoLevels=False)
            sigma = np.std(spectrogram)
            mean = np.mean(spectrogram)
            self.spectrogram_min = mean - 2*sigma # save to window state
            self.spectrogram_max = mean + 2*sigma

        def end_of_run_callback():
            QTimer.singleShot(0, worker.run) # Run worker again immediately

        #Plots To Call #addWidget adds plot #removeWidget removes plot to keep memory well
        #Add Layout to QLabel = FREQ_GRAPH
        # freqlayout = QHBoxLayout(self.FREQ_GRAPH)
        # self.FREQ_GRAPH.setLayout(freqlayout)
        # self.FREQ_GRAPH.setScaledContents(True)

        # Time plot
        time_plot = pg.PlotWidget(labels={'left': 'Amplitude', 'bottom': 'Time [microseconds]'})
        time_plot.setMouseEnabled(x=False, y=True)
        time_plot.setYRange(-1.1, 1.1)
        time_plot_curve_i = time_plot.plot([])
        time_plot_curve_q = time_plot.plot([])
        self.time_layout.addWidget(time_plot)

        # Freq plot
        freq_plot = pg.PlotWidget(labels={'left': 'PSD', 'bottom': 'Frequency [MHz]'})
        freq_plot.setMouseEnabled(x=False, y=True)
        freq_plot_curve = freq_plot.plot([])
        freq_plot.setXRange(center_freq/1e6 - sample_rate/2e6, center_freq/1e6 + sample_rate/2e6)
        freq_plot.setYRange(-30, 20)
        self.freq_layout.addWidget(freq_plot)

        # Waterfall plot
        waterfall = pg.PlotWidget(labels={'left': 'Time [s]', 'bottom': 'Frequency [MHz]'})
        imageitem = pg.ImageItem(axisOrder='col-major') # this arg is purely for performance
        waterfall.addItem(imageitem)
        waterfall.setMouseEnabled(x=False, y=False)
        self.waterfall_layout.addWidget(waterfall)

        # Colorbar for waterfall
        colorbar = pg.HistogramLUTWidget()
        colorbar.setImageItem(imageitem) # connects the bar to the waterfall imageitem
        colorbar.item.gradient.loadPreset('viridis') # set the color map, also sets the imageitem
        imageitem.setLevels((-30, 20)) # needs to come after colorbar is created for some reason
        self.waterfall_layout.addWidget(colorbar)         

        worker.time_plot_update.connect(time_plot_callback) # connect the signal to the callback
        worker.freq_plot_update.connect(freq_plot_callback)
        worker.waterfall_plot_update.connect(waterfall_plot_callback)
        worker.end_of_run.connect(end_of_run_callback)

        self.sdr_thread.started.connect(worker.run) # kicks off the worker when the thread starts
        self.sdr_thread.start()
        
        # Initialize sensor data arrays (720 data points per sensor) about 12 minutes of data
        self.data_sens1 = np.zeros(720)  # Sensor 1 (e.g., MQ4)
        self.data_sens2 = np.zeros(720)  # Sensor 2 (e.g., MQ6)
        self.data_sens3 = np.zeros(720)  # Sensor 3 (e.g., MQ135)
        self.data_sensrad = np.zeros(720) #Rad Sensor, Geiger Counter
        
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
            # try:
                # self.serial_portGPS = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
            # except Exception as e:
                # print("Error initializing GPS serial port on Linux:", e)
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

        #Manual Triggering of Garbage Collection #did something weird, disabled for further investigation, suspect
        self.gacl = QTimer(self)
        self.gacl.timeout.connect(self.run_gc)
        self.gacl.start(30000)
        
        #Gas Sensor Graph
        #Matplotlib persistant canvas
        self.graphWidget = self.findChild(QWidget, "SENSGRAPH")
        # if self.graphWidget is None:
        #     self.graph_timer.start(1000)
        
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

        #Geiger Sensor Graph
        #Matplotlib persistant canvas
        self.radGraphWidget = self.findChild(QWidget, "SELGRAPHRAD")
        if self.graphWidget is None:
            self.radGraphWidget = QWidget(self)
            #self.graph_timer.start(5000)

        #Radiation Counters for alerts
        self.last_60_cps = deque(maxlen= 60)
        self.current_cps = 0
        # self.last_60_cpm = deque(maxlen= 60)
        # self.current_cpm = 0
        # self.last_24_cph = deque(maxlen= 24)
        # self.current_cph = 0
        
        self.cpm_timer = QTimer(self)
        self.cpm_timer.timeout.connect(self.update_cpm)
        self.cpm_timer.start(1000)

        #self.cph_timer = QTimer(self)
        #self.cph_timer.timeout.connect(self.update_cph)
        #self.cph_timer.start(60000)

        #self.cpd_timer = QTimer(self)
        #self.cpd_timer.timeout.connect(self.update_cpd)
        #self.cpd_timer.start(36000000)
        
        rad_layout = QVBoxLayout(self.radGraphWidget)
        self.radGraphWidget.setLayout(rad_layout)
        self.radGraphWidget.setScaledContents(True)

        self.radfigure = Figure(figsize=(6,4))
        self.radcanvas = FigureCanvas(self.radfigure)
        rad_layout.addWidget(self.radcanvas)

        #Set Labales and title
        self.radax = self.radfigure.add_subplot(111)
        self.radax.set_title('Counts Per Second (Radiation)')
        self.radax.set_xlabel('Time (sec)')
        self.radax.set_ylabel('CPS')
        self.count = 0

        #Plot the data
        self.radline, = self.radax.plot(self.data_sensrad, color="purple", label="CPS")
            
        #add legend
        self.radax.legend()
        self.radcanvas.draw()

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

        self.radgraph_timer = QTimer(self)
        self.radgraph_timer.timeout.connect(self.update_rad_graph)

        #vault boy on main screen
        self.vaultboy = QImage("/home/marceversole/WorkingPipBoy/VaultBoy.png")
        self.vaultpix = QPixmap.fromImage(self.vaultboy)
        self.vaultlabel = QLabel()
        self.vaultlabel.setPixmap(self.vaultpix)
        self.pipboygif.addWidget(self.vaultlabel)
        self.vaultlabel.setScaledContents(True)

        QTimer.singleShot(50, self.start_fullscreen)

    def start_fullscreen(self):
        self.showFullScreen()
    
    # def handle_freq_input(self):
    #         freq_text = self.freqInput.text()
    #         try:
    #             #convert to float
    #             self.freq_val = float(self.freqInput.text())
                
    #         except ValueError:
    #             self.freqInput.setText("750.00")
    
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
                self.data_sensrad = np.roll(self.data_sensrad, -1)
                
                # Update sensor data (ensure values[0-2] are valid floats)
                self.data_sens1[-1] = float(values[0])
                self.data_sens2[-1] = float(values[1])
                self.data_sens3[-1] = float(values[2])
                self.data_sensrad[-1] = float(values[3])
                self.count = values[3]
                # self.sec4.setText(self.cps)

                self.SENS1.setText(f"MQ4: {values[0]}")
                self.SENS2.setText(f"MQ6: {values[1]}")
                self.SENS3.setText(f"MQ135: {values[2]}")
                self.sel_4.setText(f"RAD: {values[3]} CPS")
                # print(f'{values[0]},{values[1]},{values[2]},{values[3]}')
                
                # Update UI if sufficient values are provided, if the if statement doesnt read all 5 values or more, it will shutoff all serial data!!! ask me how i know
                # if len(values) >= 3:
                #     self.SENS1.setText(f"MQ4: {values[0]}")
                #     self.SENS2.setText(f"MQ6: {values[1]}")
                #     self.SENS3.setText(f"MQ135: {values[2]}")
                #     self.sel_4.setText(f"RAD: {values[3]} CPS")
                #     print(f'CPS = {values[3]}')
                #     self.TEMP.setText(f'Temp: {values[4]} F')
                #     # try:
                #     #     self.menuScreen = int(values[4])
                #     # except ValueError:
                #     #     print("Invalid menuScreen value received:", values[4])
                #     # self.update_tab()
                # else:
                #     print('No serial in data recieved')
                #     print(f'{values[0],values[1],values[2],values[3]}')
                
                # Update the graph with the new data
                self.update_graph()
                self.update_rad_graph()
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
        # lat, lon = self.get_current_gps_coordinates()  # Replace with real GPS data when available
        self.get_current_gps_coordinates()

    def update_cpm(self):
        # Append the current CPS value to the rolling deque.
        self.current_cps = int(self.count)
        self.last_60_cps.append(self.current_cps)
        #Currently returning a string, because of how we are displaying the cps, so that will need to be turned back into an int to work properly
        # Compute CPM as the sum of the last 60 CPS values.
        cpm = sum(self.last_60_cps)
        # For example, update a UI element or print the CPM.
        # print("CPM:", cpm)
        # Optionally, store the value in a variable for other processing:
        self.cpm = cpm
        self.sel_1min.setText(f'CPM: {str(self.cpm)}')
        #Adding in counter to sieverts calculation based on GM Tube M4011 conversion index 151
        sieverts = self.cpm/151
        self.min.setText(f'{round(sieverts,2)} uSv/h')

    def update_cph(self):
        # Append the current CPS value to the rolling deque.
        self.current_cpm = self.cpm
        self.last_60_cpm.append(self.current_cpm)
        # Compute CPM as the sum of the last 60 CPS values.
        cph = sum(self.last_60_cpm)
        # For example, update a UI element or print the CPM.
        # print("CPH:", cph)
        # Optionally, store the value in a variable for other processing:
        self.cph = cph
        self.hour.setText(str(self.cph))

    def update_cpd(self):
        # Append the current CPS value to the rolling deque.
        self.current_cph = self.cph
        self.last_24_cph.append(self.current_cph)
        # Compute CPM as the sum of the last 60 CPS values.
        cpd = sum(self.last_24_cph)
        # For example, update a UI element or print the CPM.
        # print("CPD:", cpd)
        # Optionally, store the value in a variable for other processing:
        self.cpd = cpd
        self.hour24.setText(str(self.cpd))

    def update_rad_graph(self):
        """
        Render a matplotlib graph of the sensor data and display it in the UI.
        The graph is saved to a BytesIO buffer, then loaded into a QPixmap.
        """
        try:
            self.radax.set_ylim(0, 20)
            self.radline.set_ydata(self.data_sensrad)            

            self.radax.set_xlim(max(0, len(self.data_sensrad) - 300), len(self.data_sensrad))

            self.radcanvas.draw_idle()
        except Exception as e:
            print("Error Updating Graph", e)
    
    def get_current_gps_coordinates(self):
        """
        Return the current GPS coordinates as (latitude, longitude).
        This function calls read_gps_data() to obtain data from the GPS hat.
        If no valid data is received, it falls back to fixed demo coordinates.
        """
        x = GGA_Read()
        if x is not None:
            self.gpsdat = list(x)
            # self.gpsdat = GGA_Read()
            # self.lat = self.gpsdat[0]
            # self.lon = self.gpsdat[1]
            # self.lon = -1*self.lon
            # self.gpsqual = self.gpsdat[4]
            self.NODATA.setText('')
            self.lat = float(self.gpsdat[0])
            self.lon = self.gpsdat[1]
            self.lon = float(self.lon) * -1
            self.UTCTime = self.gpsdat[2]
            self.gpsqual = self.gpsdat[4]
            print("GPS: Lat=", self.lat, " Lon=", self.lon, " Qual=", self.gpsqual, " UTC=", self.UTCTime)
            self.LAT.setText(f'LAT: {self.lat}')
            self.LON.setText(f'LON: {self.lon}')
            self.UTC.setText(f'UTC: {self.UTCTime}')

            # Build the JavaScript call to update the marker on the map.
            js_code = f"updateMarker({self.lat}, {self.lon});"
            # Run the JavaScript in the QWebEngineView.
            self.mapView.page().runJavaScript(js_code)
            # print(f"Updated GPS marker to lat: {lat}, lon: {lon}")
        
        else:
            self.NODATA.setText('NO SAT DATA')
            print(str(x))


        
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
        #realcap = capacity * 2
        # Check if a previous capacity exists and compare.
        if hasattr(self, 'previous_capacity'):
            if capacity > self.previous_capacity:
                self.flashProgressBar("green")
            elif capacity < self.previous_capacity:
                self.flashProgressBar("red")
            # If equal, you might choose not to change the color.
        # Store the new capacity for the next comparison.
        self.previous_capacity = capacity
        # print(f'Current Capacity = {capacity}')
        self.progressBar.setValue(int(capacity))

    def flashProgressBar(self, color):
        # Change the color of the progress bar's "chunk" (the filled portion).
        # You can customize the duration (here 500ms) as needed.
        self.progressBar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        # After 500ms, reset the style sheet back to its default.
        QTimer.singleShot(500, self.resetProgressBarColor)

    def resetProgressBarColor(self):
        # Revert to the original style (you can either set an empty style sheet
        # or restore a predefined style if you have one).
        self.progressBar.setStyleSheet("")
        
if __name__ == "__main__":
    # Use sys.argv for proper argument parsing in PySide6
    app = QApplication(sys.argv)
    #Build Absolute path to your MP4 File (in same folder as script)
    video_path = os.path.abspath("/home/marceversole/WorkingPipBoy/PipBoySplash.gif")
    audio_path = os.path.abspath("/home/marceversole/WorkingPipBoy/PipBoyStartSound.mp3")
    #Create and show the splash screen
    splash = SplashScreen(video_path, audio_path, duration=5400)
    splash.show()

    
    def start_main_app():
        window = MainWindow()
        # window.showFullScreen()
        window.show()
    
    QTimer.singleShot(3400, start_main_app)
    sys.exit(app.exec())