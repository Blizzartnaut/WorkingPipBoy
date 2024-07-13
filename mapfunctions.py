import sys
import os
import io
import folium #pip install folium
import time
import gps

session = gps.gps('localhost', '2947') #Local machine Port 2947 (default port gpsd listens to)
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout #pip install PyQt5
from PySide6.QtWebEngineWidgets import QWebEngineView #pip install PyQtWebEngine

dir_path = os.path.dirname(os.path.realpath(__file__))
mapPath = os.path.join(dir_path, 'map.html')

def create_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat,lon]).add_to(m) #This creates a marker on the map
    m.save('map.html')
    

# create_map(lat, lon)

class MapViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initTimer()

    def initUI(self):
        self.webView = QWebEngineView()
        self.webView.load(QUrl.fromLocalFile(mapPath)) #Update path while using os and absolute relative paths, this loads the current html file of the map

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.webView)

        self.setLayout(vbox)
        self.setGeometry(300,300,600,400)
        self.setWindowTitle('Folium in PyQt')
        self.show()

    def update_map(self, lat, lon): #Updates Coordinates of map
        lat, lon = self.get_current_location()
        create_map(lat, lon) #Creates html file for new coordinates
        self.webView.load(QUrl.fromLocalFile(mapPath)) #Reloads Html

    def initTimer(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_map) #connects to the update method
        self.timer.start(5000) #updates every 5000 milliseconds

    def get_current_location():
        while True:
            report = session.next()
            if report['class'] == 'TPV':    #Type of report, TPV = Time Position Velocity
                if hasattr(report, 'lat') and hasattr(report, 'lon'):
                    return (report.lat, report.lon)

def main():
    app = QApplication(sys.argv)
    ex = MapViewer()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()