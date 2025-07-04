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
import datetime

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
# from L76X import L76X
from newGPS import get_coordinates_from_serial

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

#importing database
import database
import json

#for radio
from radioControls import scan_band, seek_next, seek_previous, stong_freq, post_process_candidates, run_scan

#for adsb
from adsbsensing import fetch_adsb_data

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
    # print(f"Local HTTP server started on port {port}, serving directory: {directory}")
    return httpd

# --- PyAudio Setup ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=48000,       # Target audio sample rate
                output=True)

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
        self.freqInput.setText(f"{self.frequency/1e6:.2f}")
        self.time_plot_butt.setText("PLAY")
        self.freq_plot_butt.setText("STOP")
        self.time_plot_butt.clicked.connect(self.start_stream)
        self.freq_plot_butt.clicked.connect(self.stop_stream)
        # self.freqInput.returnPressed.connect(self.handle_freq_input)

        #Media Player Code Below
        # Setup music list UI elements
        self.musicList = QListWidget()
        self.mainLayout = QVBoxLayout()
        self.MusicList.setLayout(self.mainLayout)
        self.MusicList.setScaledContents(True)
        self.mainLayout.addWidget(self.musicList)
        self.VolSlider.valueChanged.connect(self.update_volume)
        self.mixer = alsaaudio.Mixer()

        #VolSlider style sheet
        self.VolSlider.setStyleSheet(f"""
                QSlider::handle:vertical {{
                    width: 18px:
                }}
            """)

        
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

        #Button for functions
        self.ReBoot.clicked.connect(self.reboot)
        self.ShutDown.clicked.connect(self.shutdown)
        self.FMSe.clicked.connect(self.scan_fm_band)
        self.SeekR.clicked.connect(self.seek_next_button_pressed)
        self.SeekL.clicked.connect(self.seek_previous_button_pressed)

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
        self.ZOOM_SLIDER.valueChanged.connect(self.zoom_map)

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

        # #Scan Frequency Timers
        # self.fmScan = QTimer(self)
        # self.fmScan.timeout.connect(self.scanner)
        # self.fmScan.start(600000)
        # # self.fmScan.singleShot(2000, self.scanner)
        # # self.freq_text = 102.7
        self.scannerstart = QTimer(self)
        self.scannerstart.singleShot(2000, self.start_scanning)
        
        # Graph update timer: refresh graph every 10 seconds.
        self.graph_timer = QTimer(self)
        self.graph_timer.timeout.connect(self.update_graph)

        #Gas Sensor Graph
        #Matplotlib persistant canvas
        #Using Blitting
        self.graphWidget = self.findChild(QWidget, "SENSGRAPH")
        # if self.graphWidget is None:
        #     self.graph_timer.start(1000)
        
        graph_layout = QVBoxLayout(self.graphWidget)
        self.graphWidget.setLayout(graph_layout)
        self.graphWidget.setScaledContents(True)

        self.fig_gas = Figure(figsize=(6,4))
        self.canvas_gas = FigureCanvas(self.fig_gas)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(self.canvas_gas)

        #Set Labels and title
        self.ax_gas = self.fig_gas.add_subplot(111)
        self.window_seconds = 300
        self.window_minutes = 5
        self.ax_gas.set_title(f'Past {self.window_minutes} Minutes')
        self.ax_gas.set_xlabel('Time (sec)')
        self.ax_gas.set_ylabel('Value')

        #Plot the data
        self.line1, = self.ax_gas.plot([], [], color="blue", label="MQ4")
        self.line2, = self.ax_gas.plot([], [], color="red", label="MQ6")
        self.line3, = self.ax_gas.plot([], [], color="green", label="MQ135")
            
        #add legend
        self.ax_gas.set_xlim(0, self.window_seconds)
        self.ax_gas.set_ylim(0, 1000)
        self.ax_gas.legend()
        # self.canvas_gas.draw()
        # self.bg_gas = self.canvas_gas.copy_from_bbox(self.ax_gas.bbox)

        # #Further set up initial blitting lines
        # self.ax_gas.draw_artist(self.line1)
        # self.ax_gas.draw_artist(self.line2)
        # self.ax_gas.draw_artist(self.line3)
        # self.canvas_gas.blit(self.ax_gas.bbox)

        #Geiger Sensor Graph
        #Matplotlib persistant canvas
        #adding blitting
        self.radGraphWidget = self.findChild(QWidget, "SELGRAPHRAD")
        if self.graphWidget is None:
            self.radGraphWidget = QWidget(self)
            #self.graph_timer.start(5000)

        rad_layout = QVBoxLayout(self.radGraphWidget)
        self.radGraphWidget.setLayout(rad_layout)
        self.radGraphWidget.setScaledContents(True)

        self.radfigure = Figure(figsize=(5,3))
        self.canvas_rad = FigureCanvas(self.radfigure)
        rad_layout.addWidget(self.canvas_rad)

        #Set Labales and title
        self.ax_rad = self.radfigure.add_subplot(111)
        self.ax_rad.set_title('Counts Per Second (Radiation)')
        self.ax_rad.set_xlim(0, self.window_seconds)
        self.ax_rad.set_ylim(0, 200) 
        self.ax_rad.set_xlabel('Time (sec)')
        self.ax_rad.set_ylabel('CPS')
        self.count = 0

        #Plot the data
        self.radline, = self.ax_rad.plot([], [], color="purple", label="CPS")
            
        #add legend
        self.ax_rad.legend()
        # self.canvas_rad.draw()
        # self.bg_rad = self.canvas_rad.copy_from_bbox(self.ax_rad.bbox)

        # #For blitting
        # self.ax_rad.draw_artist(self.radline)
        # self.canvas_rad.blit(self.ax_rad.bbox)

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

        self.adsb_timer = QTimer(self)
        self.adsb_timer.timeout.connect(self.update_aircraft_markers)
        self.adsb_timer.start(5000)
        self.start_adsb_start = QTimer(self)
        self.start_adsb_start.singleShot(1000, self.adsb_start)
        

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
        
        # NEW: Timer to update GPS marker (calls update_gps_marker method) #Do not reenable until new gps is installed and understood how it works
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

        #Start database
        database.init_db()

        QTimer.singleShot(20, self.start_fullscreen)

    def start_fullscreen(self):
        self.showFullScreen()

    def showEvent(self, event):
        """
        Override Qt’s showEvent so that, once the window is laid out and shown,
        we capture the true background (canvas size is final) and paint our empty
        line artists into that background. Only then do we start the blit timers.
        """
        super().showEvent(event)

        # —–––––––––––––––––––––––––––––––––
        # STEP 1: Force a full draw of each FigureCanvas (now that it’s sized correctly)
        self.canvas_gas.draw()
        self.bg_gas = self.canvas_gas.copy_from_bbox(self.ax_gas.bbox)
        # Draw your (empty) gas‐sensor lines into that background:
        self.ax_gas.draw_artist(self.line1)
        self.ax_gas.draw_artist(self.line2)
        self.ax_gas.draw_artist(self.line3)
        # Blit that first frame to “prime” the canvas:
        self.canvas_gas.blit(self.ax_gas.bbox)

        # —–––––––––––––––––––––––––––––––––
        # STEP 2: Do the exact same for the radiation canvas
        self.canvas_rad.draw()
        self.bg_rad = self.canvas_rad.copy_from_bbox(self.ax_rad.bbox)
        self.ax_rad.draw_artist(self.radline)
        self.canvas_rad.blit(self.ax_rad.bbox)

        # —–––––––––––––––––––––––––––––––––
        # STEP 3: Now that the backgrounds are captured, start the update timers
        # self.graph_timer.start(1000)     # gas timer at 1 Hz
        # self.radgraph_timer.start(1000)  # radiation timer at 1 Hz

    def start_scanning(self):
        #Scan Frequency Timers
        self.fmScan = QTimer(self)
        self.fmScan.timeout.connect(self.scanner)
        self.fmScan.start(600000)
        # self.fmScan.singleShot(2000, self.scanner)
        # self.freq_text = 102.7
    
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
            
            if self.length == None:
                self.auto_play()


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
        self.frequency = self.new_freq
        #small delay to allow time for commands to terminate
        time.sleep(0.5)
        self.start_stream()
        self.freqInput.setText(f"{self.frequency/1e6:.2f}")

    def handle_freq_input(self):
        # freq_text = self.freqInput.text().strip()
        
        try:
            # Convert the input to a float. Assume input is in MHz.
            new_freq_mhz = float(self.freq_text)
            new_freq_hz = new_freq_mhz * 1e6  # convert MHz to Hz
            self.new_freq = new_freq_hz
            self.freqInput.setText(f"{self.frequency/1e6:.2f} MHz")
            
            # If the radio is already running, change frequency immediately.
            if self.process:
                self.change_frequency()
            else:
                # If the radio isn't playing, just update the stored frequency.
                self.frequency = self.new_freq
            # Optionally, clear the text input.
            self.freqInput.clear()
        except ValueError:
            # If the conversion fails, display an error message.
            self.freqInput.setText("Invalid frequency")

    def insert_database(self):
        #Inserts sensor and gps data into database for later recall
        database.insert_sensor_data(self.data_sens1, self.data_sens2, self.data_sens3, self.data_sensrad, self.lat, self.lon)
        print(f"Inserting into DB: {self.data_sens1 =}, {self.data_sens2 =}, {self.data_sens3 =}, {self.data_sensrad =}, {self.lat=}, {self.lon=}")

    def load_sensor_history(self, minutes=5):
        """
        Query the last `minutes` of data and return:
          x = [seconds since first point, …],
          y1, y2, y3 = sensor1/2/3 lists,
          y4 = sensor4 list.
        """
        rows = database.query_recent_data(minutes)
        if not rows:
            return [], [], [], [], []

        # Parse timestamps and readings
        times = [datetime.datetime.fromisoformat(r[0]) for r in rows]
        t0 = times[0]
        x = [(t - t0).total_seconds() for t in times]

        y1 = [r[1] for r in rows]
        y2 = [r[2] for r in rows]
        y3 = [r[3] for r in rows]
        y4 = [r[4] for r in rows]
        return x, y1, y2, y3, y4
    
    def update(self):
        """
        Update date and time labels on the UI.
        Ensure that the UI file defines labels with the object names 'DATE' and 'TIME';
        otherwise, update these names to match the UI.
        """
        self.DATE.setText("Date: " + QDate.currentDate().toString())
        self.TIME.setText("Time: " + QTime.currentTime().toString())
    
    def read_Serial(self):
        if hasattr(self, 'serial_port') and self.serial_port.in_waiting > 0:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                vals = line.split(',')
                # Parse the four sensor readings as floats
                s1, s2, s3, s4 = map(float, vals[:4])
                # (If you later send menuScreen or volumeD, grab those separately.)

                # Roll and update your time‐series arrays as before
                self.data_sens1 = np.roll(self.data_sens1, -1)
                self.data_sens1[-1] = s1
                self.data_sens2 = np.roll(self.data_sens2, -1)
                self.data_sens2[-1] = s2
                self.data_sens3 = np.roll(self.data_sens3, -1)
                self.data_sens3[-1] = s3
                self.data_sensrad = np.roll(self.data_sensrad, -1)
                self.data_sensrad[-1] = s4

                # Update your labels
                self.SENS1.setText(f"MQ4: {s1}")
                self.SENS2.setText(f"MQ6: {s2}")
                self.SENS3.setText(f"MQ135: {s3}")
                self.sel_4.setText(f"RAD: {s4} CPS")

                # Make sure you have up-to-date GPS
                lat, lon = getattr(self, 'lat', None), getattr(self, 'lon', None)

                # Call your database API with scalars
                database.insert_sensor_data(s1, s2, s3, s4, lat, lon)

                # Redraw your graphs
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
            x, y1, y2, y3, _ = self.load_sensor_history(minutes=5)
            if not x:
                return  # no data yet

            #Restore background
            self.canvas_gas.restore_region(self.bg_gas)

            #Update the line data
            self.line1.set_data(x, y1)
            self.line2.set_data(x, y2)
            self.line3.set_data(x, y3)

            #Draw only those artists onto the restored background
            self.ax_gas.draw_artist(self.line1)
            self.ax_gas.draw_artist(self.line2)
            self.ax_gas.draw_artist(self.line3)

            #Blit the updated Axes rectangle to the screen
            self.canvas_gas.blit(self.ax_gas.bbox)

            # # Update your existing lines:
            # self.line1.set_xdata(x)
            # self.line1.set_ydata(y1)
            # self.line2.set_xdata(x)
            # self.line2.set_ydata(y2)
            # self.line3.set_xdata(x)
            # self.line3.set_ydata(y3)

            # # Rescale axes to fit new data
            # self.ax.relim()
            # self.ax.autoscale_view()

            # self.ax.set_title('Past 10 Minutes')
            # self.ax.set_xlabel('Seconds ago')
            # self.canvas.draw_idle()
            # t0 = time.time()
            # self.canvas.draw_idle()
            # print("Draw took", (time.time() - t0)*1000, "ms")
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
        self.update_gps_path_on_map()

    def zoom_map(self, value):
        # self.zoomlevel = self.ZOOM_SLIDER.value
        js_codeMap = f"map.setZoom({value});"
        # Run the JavaScript in the QWebEngineView.
        self.mapView.page().runJavaScript(js_codeMap)

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
            """
            Plot the geiger data (sensor4) from DB history.
            """
            x, _, _, _, y4 = self.load_sensor_history(minutes=5)
            if not x:
                return

            self.canvas_rad.restore_region(self.bg_rad)

            self.radline.set_data(x, y4)
            self.ax_rad.draw_artist(self.radline)

            self.canvas_rad.blit(self.ax_rad.bbox)

            # self.radline.set_xdata(x)
            # self.radline.set_ydata(y4)

            # self.radax.relim()
            # self.radax.autoscale_view()

            # self.radax.set_title('Radiation CPS — Past 5 Minutes')
            # self.radax.set_xlabel('Seconds ago')
            # self.radcanvas.draw_idle()
        except Exception as e:
            print("Error Updating Graph", e)
    
    def get_current_gps_coordinates(self):
                
        self.lat, self.lon = get_coordinates_from_serial()
        if self.lat is not None and self.lon is not None:
            # Build the JavaScript call to update the marker on the map.
            js_code = f"updateMarker({self.lat}, {self.lon});"
            # Run the JavaScript in the QWebEngineView.
            self.mapView.page().runJavaScript(js_code)
            # print(f"Updated GPS marker to lat: {lat}, lon: {lon}")

    def update_gps_path_on_map(self):
        # Query the database for the last 60 minutes of GPS coordinates.
        gps_points = database.query_recent_gps(minutes=60)
        # Convert the list to JSON.
        gps_points_json = json.dumps(gps_points)
        # Build the JavaScript call.
        js_code = f"updateGPSPath({gps_points_json});"
        # Run the JavaScript in the QWebEngineView.
        self.mapView.page().runJavaScript(js_code)
        
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
        self.TimeREM.setText(str(info.get("runtime_empty", "N/A")))

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

        if info.get('charging_state', "N/A") == 'Fast Charging' or info.get('charging_state', "N/A") == 'Charging':
            self.progressBar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {"green"};
                    font: bold 15px:
                    qproperty-alignment: 'AlignVCenter | AlignLeft':
                }}
            """)
        elif info.get('charging_state', "N/A") == 'Dischaging':
            self.progressBar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {"red"};
                    font: bold 15px:
                    qproperty-alignment: 'AlignVCenter | AlignLeft':
                }}
            """)

    # def flashProgressBar(self, color):
    #     # Change the color of the progress bar's "chunk" (the filled portion).
    #     # You can customize the duration (here 500ms) as needed.
    #     self.progressBar.setStyleSheet(f"""
    #         QProgressBar::chunk {{
    #             background-color: {color};
    #         }}
    #     """)
    #     # After 500ms, reset the style sheet back to its default.
    #     QTimer.singleShot(500, self.resetProgressBarColor)

    # def resetProgressBarColor(self):
    #     # Revert to the original style (you can either set an empty style sheet
    #     # or restore a predefined style if you have one).
    #     self.progressBar.setStyleSheet("")

    # @Slot(object)
    # def update_spectrum(self, spectrum):
    #     # This method is called by SDRWorker with the computed spectrum.
    #     # Update your curve with the new data.
    #     self.curve.setData(spectrum)

    def reboot(self):
        cmd = (
            f"sudo reboot"
        )
        # Launch command as subprocess
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid) #keeps track of the process for later

    def shutdown(self):
        cmd = (
            f"sudo shutdown -h now"
        )
        # Launch command as subprocess
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid) #keeps track of the process for later

    def scan_fm_band(self):
        # For FM, use a range of 88 MHz to 108 MHz, step size 200 kHz,
        # integration time of 0.5 seconds, and a threshold (e.g., -80 dB).
        # fm_candidates = scan_band(
        #     band_name="FM",
        #     start_freq=88e6,
        #     end_freq=108e6,
        #     step=200000,         # 200 kHz
        #     integration_time=10,
        #     threshold=10,      # Adjust threshold as needed
        #     output_csv="fm_scan.csv"
        # )
        # # Store the candidate list in your class.
        fm_candidates = stong_freq()
        self.candidate_list = fm_candidates

        fm_candidates_snapped = post_process_candidates(fm_candidates)


        # Find the index in candidate_list that is closest to the current frequency:
        if fm_candidates_snapped:
            self.current_candidate = min(fm_candidates, key=lambda x: abs(x - self.frequency))
            self.candidatesLabel.setText(f'Found {len(self.candidate_list)} Candidates!')
        else:
            print("No strong candidates found!")

    def seek_next_button_pressed(self):
        if self.candidate_list:
            self.new_freq = seek_next(self.frequency, self.candidate_list)
            # self.set_frequency(new_freq) #I think this might cause problems, testing
            self.change_frequency()

    def seek_previous_button_pressed(self):
        if self.candidate_list:
            self.new_freq = seek_previous(self.frequency, self.candidate_list)
            # self.set_frequency(new_freq)
            self.change_frequency()

    def scanner(self):
        scan_thread = threading.Thread(target=run_scan, daemon=True)
        scan_thread.start()

    def update_aircraft_markers(self):
        adsb_data = fetch_adsb_data()
        # Convert the list to a JSON string
        adsb_json = json.dumps(adsb_data)
        # Call the JavaScript function to update markers:
        js_code = f"updateAircraftMarkers({adsb_json});"
        self.mapView.page().runJavaScript(js_code)

    def adsb_start(self):
        cmd = f"/home/marceversole/dump1090/dump1090 --interactive --net"
        self.adsb_process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)

    def closeEvent(self, event):
        # When the program is closing, kill the ADS-B process (if running)
        if self.adsb_process:
            os.killpg(os.getpgid(self.adsb_process.pid), signal.SIGTERM)
        event.accept()
        
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