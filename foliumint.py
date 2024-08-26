import sys
import io
import folium #pip install folium
import time
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout #pip install PyQt5
from PyQt5.QtWebEngineWidgets import QWebEngineView #pip install PyQtWebEngine

global coord
coord = [0,0]

x = True

class Mapping(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Folium in PyQt Example')
        self.window_width, self.window_height = 1600, 1200
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # coord = []
        coord = [41.0120, -76.8477] # North = + , South = - , East = +, West = -, (Latitude, Longitude)

        m = folium.Map(
            title='Milton Test Map',
            zoom_start=13,
            location=coord
        ) #Starts Mapping Function using Folium and provided coordinates

        #Saves map data to data object
        data = io.BytesIO()
        m.save(data, close_file=False)

        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        layout.addWidget(webView)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('''
        QWidget {
            font-size:35px;
        }
    ''')

    mapp = Mapping()
    mapp.show()

    # while x == True: #Need to test updating of coordinates
    #     coord[0] = coord[0] + 0.01
    #     coord[1] = coord[1] + 0.01
    #     time.sleep(10)

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Closing Window')