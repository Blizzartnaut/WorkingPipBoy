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
import subprocess
import signal

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QListWidget, QProgressBar, QGridLayout, QSlider, QLabel, QHBoxLayout, QPushButton, QComboBox, QRadioButton, QSizePolicy
from PySide6.QtCore import QTimer, QDate, QTime, QIODevice, QUrl, Signal, QSize, Qt, QThread, QObject, Slot
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

#Battery Monitoring
from battery import get_battery_info

#Import GPS Mapping Functions
# from gps_lib import GGA_Read, RMC_Read, GSV_Read

#For RTL-SDR
from rtlsdr import *
from pylab import *
import pyaudio
import asyncio
from qasync import QEventLoop, asyncSlot

#for music
import vlc
import alsaaudio

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

# --- PyAudio Setup ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=48000,       # Target audio sample rate
                output=True)

# class SDRWorker():
#     async def run(self, update_callback):
#         sdr = RtlSdr()
#         sdr.sample_rate = 2.4e6
#         sdr.center_freq = 100e6
#         sdr.gain = 'auto'
#         # Stream samples asynchronously
#         async for samples in sdr.stream():
#             # Compute a spectrum (FFT) of the samples
#             spectrum = np.abs(np.fft.fftshift(np.fft.fft(samples)))
#             update_callback(spectrum)
#             await asyncio.sleep(0)  # yield control to the event loop

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

        # Initial Freq should be in hz, #e6 means MHz (specifically means a Mega or a million)
        self.frequency = 102.7e6
        self.process = None
        self.freqInput.setText(str(self.frequency))
        self.time_plot_butt.setText("PLAY")
        self.freq_plot_butt.setText("STOP")
        self.time_plot_butt.clicked.connect(self.start_stream)
        self.freq_plot_butt.clicked.connect(self.stop_stream)
        self.freqInput.returnPressed.connect(self.handle_freq_input)

        #Media Player Code Below
        # Setup music list UI elements
        self.musicList = QListWidget()
        self.mainLayout = QVBoxLayout()
        self.MusicList.setLayout(self.mainLayout)
        self.MusicList.setScaledContents(True)
        self.mainLayout.addWidget(self.musicList)
        self.VolSlider.valueChanged.connect(self.update_volume)
        self.mixer = alsaaudio.Mixer()
        
        # Playlist management
        self.musicDir = os.path.abspath("music")  # Ensure this folder exists.
        self.musicFiles = []
        self.currentIndex = 0
        if os.path.isdir(self.musicDir):
            for file in os.listdir(self.musicDir):
                if file.lower().endswith(".mp3"):
                    fullPath = os.path.join(self.musicDir, file)
                    self.musicFiles.append(fullPath)
                    self.musicList.addItem(file)
        
        # Remove QMediaPlayer setup since we are using VLC exclusively.
        # self.player = QMediaPlayer() ... etc.
        
        # Set up VLC player exclusively:
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        # Use self.musicFiles (not self.media_files) and self.currentIndex consistently.
        if self.musicFiles:
            self.set_media(self.musicFiles[self.currentIndex])
        
        # Connect VLC player control buttons
        self.PLAY.clicked.connect(self.play)
        self.STOP.clicked.connect(self.stop)
        self.NEXT.clicked.connect(self.next_track)
        self.PAUSE.clicked.connect(self.pause_resume)
        self.musicList.itemClicked.connect(self.listItemClicked)

        # Timer to update progress (if desired)
        self.dur_timer = QTimer(self)
        self.dur_timer.timeout.connect(self.update_progress)
        self.dur_timer.start(500)

        # Timer to check on volume potentiometer
        self.vol_timer = QTimer(self)
        self.vol_timer.timeout.connect(self.pot_vol_update)
        self.vol_timer.start(500)

        # Set up VLC event manager to listen for end-of-media events
        # events = self.player.event_manager()
        # events.event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)

        # if self.player.mediaStatusChanged:
        #     self.next_track()

        self.progressBar_2.setMinimum(0)
        self.progressBar_2.setMaximum(100)     
        
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

        #Timer for battery status
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(2000)

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
        # local_map_path = os.path.abspath("pipboy_map.html")
        self.mapView.load(QUrl("http://localhost:8000/pipboy_map.html"))
        layout.addWidget(self.mapView)
        
        # # NEW: Timer to update GPS marker (calls update_gps_marker method) #Do not reenable until new gps is installed and understood how it works
        # self.gps_timer = QTimer(self)
        # self.gps_timer.timeout.connect(self.update_gps_marker)
        # self.gps_timer.start(2000)  # Update every 2 seconds (adjust as needed)

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

        QTimer.singleShot(20, self.start_fullscreen)

    def start_fullscreen(self):
        self.showFullScreen()
    
    # # RTL SDR Setup
    #     @asyncSlot(object)
    #     async def update_spectrum(self, spectrum):
    #         # Update the graph with new spectrum data.
    #         self.curve.setData(spectrum)

    def set_current_track(self, index):
        """Set the current track for the VLC player."""
        if 0 <= index < len(self.musicFiles):
            self.currentIndex = index
            if self.player:
                self.player.stop()
            
            # Attach event to auto-play the next track when current one ends
            # event_manager = self.player.event_manager()
            # event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._end_callback)

    # def _end_callback(self, event):
    #     # This callback is invoked when the track finishes playing.
    #     # Make sure you call it in a thread-safe way if you're updating the UI.
    #     self.next_track()
    def update_volume(self, value):
        #Value should be between 0 and 100, as set in ui
        self.mixer.setvolume(value)

    def set_media(self, file_path):
        if os.path.exists(file_path):
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
        else:
            print(f"Media file not found: {file_path}")
    
    def play(self):
        if self.player:
            self.player.play()
            self.hold = True
        if self.process:
            self.stop_stream()
    
    def stop(self):
        if self.player:
            self.player.stop()
    
    def auto_play(self):
        self.songNextTimer = QTimer()
        self.songNextTimer.timeout.connect(self.next_track)
        self.songNextTimer.setSingleShot(True) #allows this timer function to be called only once per function call, timers normally repeat
        self.songNextTimer.start(1400)

    def pause_resume(self):
        if self.player:
            self.player.pause()
    
    def next_track(self):
        self.currentIndex = (self.currentIndex + 1) % len(self.musicFiles)
        self.set_media(self.musicFiles[self.currentIndex])
        self.updateLabels()
        self.play()
    
    def listItemClicked(self, item):
        row = self.musicList.row(item)
        self.currentIndex = row
        self.set_media(self.musicFiles[self.currentIndex])
        self.updateLabels()
        self.play()
    
    def updateLabels(self):
        if self.musicFiles:
            current_song = os.path.basename(self.musicFiles[self.currentIndex])
            self.CurrentPlay.setText(f"Current Play: {current_song}")
            next_index = (self.currentIndex + 1) % len(self.musicFiles)
            next_song = os.path.basename(self.musicFiles[next_index])
            self.NextUp.setText(f"Next Up: {next_song}")
            # self.SongTime.setText(f'{self.player.get_length()/1000}') Need to convert using time to MM:SS
        else:
            self.CurrentPlay.setText("Current Play: None")
            self.NextUp.setText("Next Up: None")
    
    def update_progress(self):
        # Example: Update a progress bar based on VLC's playback time.
        self.length = self.player.get_length()  # in ms
        if self.length > 0:
            self.current = self.player.get_time()  # in ms
            self.percent = int((self.current / self.length) * 100)
            self.SongProgress.setValue(self.percent)
            self.SongTime.setText(self.convert_time(self.length))
            if self.percent >= 98: #allows us to catch the last bit of the song, calls everytime update_progress is
                # timer
                # QTimer.singleShot((self.length/98), self.next_track)
                while self.hold == True: #True is set whenever self.play() is called, but then is set to false as soon as this is called, allowing it to run only once per song
                    self.hold = False #so it doesnt trigger multiple times per song
                    QTimer.singleShot((self.length/98), self.auto_play) #sets a single shot timer to a time relative to the length of the song, in an attempt to give just enough of a break between songs


        # if self.percent >= 98: #percent hasnt been declared yet, outside of the if statement its in.
            # QTimer.singleShot((self.length/0.01), self.next_track)
            # print(f'{self.length}, {self.length/0.01}') #Why Would i do this, to increase the track time? Might have worked if i divided by whole numbers.
    
    def on_end_reached(self, event):
        self.next_track()

    def pot_vol_update(self):
        # print(f'Vol: {self.volumeD}')
        if self.volumeD != None:
            self.mixer.setvolume(int(self.volumeD))
            self.VolSlider.setSliderPosition(int(self.volumeD))

    def convert_time(self, milli):
        sec = (milli // 1000) % 60
        min = (milli // (1000*60)) % 60
        return f"{min}:{sec}"

    def start_stream(self):
        #Start rtl_fm wit current frequency using wideband fm mode (-M wbfm)
        # Build command string. With parameters:
        # -f: Frequency in Hz
        # -M wbfm: Wideband FM Demodulation (other modes exist as well read docs)
        # -s: sample rate (default is 2048e3, 2.048MS/s)
        # -r: resampling rate for audio out
        # -g: optional parameter to hard set gain parameter (0 or dont include for auto gain)
        cmd = (
            f"rtl_fm -f {self.frequency} -M wbfm -s 2048000 -r 48000 | aplay -r 48000 -f S16_LE"
        )
        # Launch command as subprocess
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid) #keeps track of the process for later
        # print(f'{cmd}')
        self.stop()

    def stop_stream(self):
        #Terminate rtl_fm subprocess (if you want quiet, or use media player)
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM) #should kill the entire process, freeing up the shell for usage later
            self.process.wait()
            self.process = None

    def change_frequency(self):
        self.stop_stream()
        self.frequency = self.newFreq
        #small delay to allow time for commands to terminate
        time.sleep(0.5)
        self.start_stream()

    def handle_freq_input(self):
        freq_text = self.freqInput.text().strip()
        try:
            # Convert the input to a float. Assume input is in MHz.
            new_freq_mhz = float(freq_text)
            new_freq_hz = new_freq_mhz * 1e6  # convert MHz to Hz
            self.newFreq = new_freq_hz
            self.freqInput.setText(f"{self.frequency/1e6:.2f} MHz")
            
            # If the radio is already running, change frequency immediately.
            if self.process:
                self.change_frequency()
            else:
                # If the radio isn't playing, just update the stored frequency.
                self.frequency = self.newFreq
            # Optionally, clear the text input.
            self.freqInput.clear()
        except ValueError:
            # If the conversion fails, display an error message.
            self.freqInput.setText("Invalid frequency")

    
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
                self.volumeD = values[7]
                # self.sec4.setText(self.cps)

                self.SENS1.setText(f"MQ4: {values[0]}")
                self.SENS2.setText(f"MQ6: {values[1]}")
                self.SENS3.setText(f"MQ135: {values[2]}")
                self.sel_4.setText(f"RAD: {values[3]} CPS")
                # print(f'{values[0]},{values[1]},{values[2]},{values[3]}')
                
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
            # print(str(x))


        
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
        # capacity = self.read_capacity()
        # #realcap = capacity * 2
        # # Check if a previous capacity exists and compare.
        # if hasattr(self, 'previous_capacity'):
        #     if capacity > self.previous_capacity:
        #         self.flashProgressBar("green")
        #     elif capacity < self.previous_capacity:
        #         self.flashProgressBar("red") #Original Battery

        info = get_battery_info()

        capacity = info.get('battery_percent', 0)

        # If equal, you might choose not to change the color.
        # Store the new capacity for the next comparison.
        self.previous_capacity = capacity
        # print(f'Current Capacity = {capacity}')
        self.progressBar.setValue(int(capacity))

        if info.get('low_warning', False):
            self.Warn1.setText('Low Voltage!')
            self.Warn2.setText('Low Voltage!')
            self.Warn3.setText('Low Voltage!')
            self.Warn4.setText('Low Voltage!')
            self.Warn5.setText('Low Voltage!')
            self.Warn6.setText('Low Voltage!')
        else:
            self.Warn1.setText('')
            self.Warn2.setText('')
            self.Warn3.setText('')
            self.Warn4.setText('')
            self.Warn5.setText('')
            self.Warn6.setText('')

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

    # @Slot(object)
    # def update_spectrum(self, spectrum):
    #     # This method is called by SDRWorker with the computed spectrum.
    #     # Update your curve with the new data.
    #     self.curve.setData(spectrum)
        
async def main():
    # async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Show splash screen first (if desired)
    video_path = os.path.abspath("/home/marceversole/WorkingPipBoy/PipBoySplash.gif")
    audio_path = os.path.abspath("/home/marceversole/WorkingPipBoy/PipBoyStartSound.mp3")
    splash = SplashScreen(video_path, audio_path, duration=5400)
    splash.show()

    # After splash, create and show the main window
    QTimer.singleShot(5400, lambda: splash.close())
    await asyncio.sleep(5)  # Wait a bit more than splash duration

    window = MainWindow()
    window.show()

    # worker = SDRWorker()
    # Launch SDR streaming in the background; it calls update_spectrum as data arrives.
    # asyncio.create_task(worker.run(window.update_spectrum))

    await loop.run_forever()

if __name__ == '__main__':
    asyncio.run(main())