# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pipboy.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMainWindow,
    QMenuBar, QProgressBar, QRadioButton, QSizePolicy,
    QSlider, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(803, 650)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 800, 600))
        font = QFont()
        font.setPointSize(15)
        self.tabWidget.setFont(font)
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.main = QWidget()
        self.main.setObjectName(u"main")
        self.progressBar = QProgressBar(self.main)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QRect(10, 10, 61, 171))
        self.progressBar.setValue(24)
        self.progressBar.setOrientation(Qt.Vertical)
        self.progressBar_2 = QProgressBar(self.main)
        self.progressBar_2.setObjectName(u"progressBar_2")
        self.progressBar_2.setGeometry(QRect(720, 10, 61, 171))
        self.progressBar_2.setValue(24)
        self.progressBar_2.setOrientation(Qt.Vertical)
        self.TIME = QLabel(self.main)
        self.TIME.setObjectName(u"TIME")
        self.TIME.setGeometry(QRect(10, 490, 201, 51))
        self.DATE = QLabel(self.main)
        self.DATE.setObjectName(u"DATE")
        self.DATE.setGeometry(QRect(540, 490, 241, 51))
        self.alarm_rad = QFrame(self.main)
        self.alarm_rad.setObjectName(u"alarm_rad")
        self.alarm_rad.setGeometry(QRect(570, 330, 200, 120))
        self.alarm_rad.setStyleSheet(u"background-color: rgb(255, 0, 0);")
        self.alarm_rad.setFrameShape(QFrame.StyledPanel)
        self.alarm_rad.setFrameShadow(QFrame.Raised)
        self.radSensorStatus = QLabel(self.alarm_rad)
        self.radSensorStatus.setObjectName(u"radSensorStatus")
        self.radSensorStatus.setGeometry(QRect(4, 5, 191, 111))
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.radSensorStatus.setFont(font1)
        self.radSensorStatus.setAlignment(Qt.AlignCenter)
        self.alarm_airsensor = QFrame(self.main)
        self.alarm_airsensor.setObjectName(u"alarm_airsensor")
        self.alarm_airsensor.setGeometry(QRect(20, 330, 200, 120))
        self.alarm_airsensor.setStyleSheet(u"background-color: rgb(255, 0, 0);")
        self.alarm_airsensor.setFrameShape(QFrame.StyledPanel)
        self.alarm_airsensor.setFrameShadow(QFrame.Raised)
        self.airSensorStatus = QLabel(self.alarm_airsensor)
        self.airSensorStatus.setObjectName(u"airSensorStatus")
        self.airSensorStatus.setGeometry(QRect(4, 5, 191, 111))
        self.airSensorStatus.setFont(font1)
        self.airSensorStatus.setAlignment(Qt.AlignCenter)
        self.tabWidget.addTab(self.main, "")
        self.air = QWidget()
        self.air.setObjectName(u"air")
        self.verticalLayoutWidget = QWidget(self.air)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 171, 541))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.SENS1 = QLabel(self.verticalLayoutWidget)
        self.SENS1.setObjectName(u"SENS1")

        self.verticalLayout.addWidget(self.SENS1)

        self.SENS2 = QLabel(self.verticalLayoutWidget)
        self.SENS2.setObjectName(u"SENS2")

        self.verticalLayout.addWidget(self.SENS2)

        self.SENS3 = QLabel(self.verticalLayoutWidget)
        self.SENS3.setObjectName(u"SENS3")

        self.verticalLayout.addWidget(self.SENS3)

        self.SENS4 = QLabel(self.verticalLayoutWidget)
        self.SENS4.setObjectName(u"SENS4")

        self.verticalLayout.addWidget(self.SENS4)

        self.SENS5 = QLabel(self.verticalLayoutWidget)
        self.SENS5.setObjectName(u"SENS5")

        self.verticalLayout.addWidget(self.SENS5)

        self.SENS6 = QLabel(self.verticalLayoutWidget)
        self.SENS6.setObjectName(u"SENS6")

        self.verticalLayout.addWidget(self.SENS6)

        self.SENS7 = QLabel(self.verticalLayoutWidget)
        self.SENS7.setObjectName(u"SENS7")

        self.verticalLayout.addWidget(self.SENS7)

        self.SENS8 = QLabel(self.verticalLayoutWidget)
        self.SENS8.setObjectName(u"SENS8")

        self.verticalLayout.addWidget(self.SENS8)

        self.TEMP = QLabel(self.air)
        self.TEMP.setObjectName(u"TEMP")
        self.TEMP.setGeometry(QRect(520, 10, 261, 51))
        self.SENSGRAPH = QLabel(self.air)
        self.SENSGRAPH.setObjectName(u"SENSGRAPH")
        self.SENSGRAPH.setGeometry(QRect(254, 115, 521, 431))
        self.tabWidget.addTab(self.air, "")
        self.rad = QWidget()
        self.rad.setObjectName(u"rad")
        self.verticalLayoutWidget_2 = QWidget(self.rad)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(190, 170, 141, 361))
        self.verticalLayout_2 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.sec4 = QLabel(self.verticalLayoutWidget_2)
        self.sec4.setObjectName(u"sec4")

        self.verticalLayout_2.addWidget(self.sec4)

        self.min = QLabel(self.verticalLayoutWidget_2)
        self.min.setObjectName(u"min")

        self.verticalLayout_2.addWidget(self.min)

        self.hour = QLabel(self.verticalLayoutWidget_2)
        self.hour.setObjectName(u"hour")

        self.verticalLayout_2.addWidget(self.hour)

        self.hour24 = QLabel(self.verticalLayoutWidget_2)
        self.hour24.setObjectName(u"hour24")

        self.verticalLayout_2.addWidget(self.hour24)

        self.lifetime = QLabel(self.verticalLayoutWidget_2)
        self.lifetime.setObjectName(u"lifetime")

        self.verticalLayout_2.addWidget(self.lifetime)

        self.SELGRAPHRAD = QLabel(self.rad)
        self.SELGRAPHRAD.setObjectName(u"SELGRAPHRAD")
        self.SELGRAPHRAD.setGeometry(QRect(350, 100, 441, 451))
        self.verticalLayoutWidget_3 = QWidget(self.rad)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayoutWidget_3.setGeometry(QRect(0, 160, 187, 391))
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.sel_4 = QRadioButton(self.verticalLayoutWidget_3)
        self.sel_4.setObjectName(u"sel_4")

        self.verticalLayout_3.addWidget(self.sel_4)

        self.sel_1min = QRadioButton(self.verticalLayoutWidget_3)
        self.sel_1min.setObjectName(u"sel_1min")

        self.verticalLayout_3.addWidget(self.sel_1min)

        self.sel_1hour = QRadioButton(self.verticalLayoutWidget_3)
        self.sel_1hour.setObjectName(u"sel_1hour")

        self.verticalLayout_3.addWidget(self.sel_1hour)

        self.sel_24h = QRadioButton(self.verticalLayoutWidget_3)
        self.sel_24h.setObjectName(u"sel_24h")

        self.verticalLayout_3.addWidget(self.sel_24h)

        self.sel_life = QRadioButton(self.verticalLayoutWidget_3)
        self.sel_life.setObjectName(u"sel_life")

        self.verticalLayout_3.addWidget(self.sel_life)

        self.tabWidget.addTab(self.rad, "")
        self.map = QWidget()
        self.map.setObjectName(u"map")
        self.OSM = QRadioButton(self.map)
        self.OSM.setObjectName(u"OSM")
        self.OSM.setGeometry(QRect(20, 420, 131, 20))
        self.TERRAIN = QRadioButton(self.map)
        self.TERRAIN.setObjectName(u"TERRAIN")
        self.TERRAIN.setGeometry(QRect(20, 470, 131, 20))
        self.HILL = QRadioButton(self.map)
        self.HILL.setObjectName(u"HILL")
        self.HILL.setGeometry(QRect(20, 520, 131, 20))
        self.ZOOM_SLIDER = QSlider(self.map)
        self.ZOOM_SLIDER.setObjectName(u"ZOOM_SLIDER")
        self.ZOOM_SLIDER.setGeometry(QRect(30, 119, 41, 261))
        self.ZOOM_SLIDER.setOrientation(Qt.Vertical)
        self.MAP = QLabel(self.map)
        self.MAP.setObjectName(u"MAP")
        self.MAP.setGeometry(QRect(204, 19, 581, 531))
        self.tabWidget.addTab(self.map, "")
        self.radio = QWidget()
        self.radio.setObjectName(u"radio")
        self.MENU2 = QTabWidget(self.radio)
        self.MENU2.setObjectName(u"MENU2")
        self.MENU2.setGeometry(QRect(0, 0, 800, 565))
        self.RADIO = QWidget()
        self.RADIO.setObjectName(u"RADIO")
        self.FREQ = QLabel(self.RADIO)
        self.FREQ.setObjectName(u"FREQ")
        self.FREQ.setGeometry(QRect(10, 10, 341, 41))
        self.FREQ_GRAPH = QLabel(self.RADIO)
        self.FREQ_GRAPH.setObjectName(u"FREQ_GRAPH")
        self.FREQ_GRAPH.setGeometry(QRect(14, 55, 761, 451))
        self.MENU2.addTab(self.RADIO, "")
        self.SOURCE_FIND = QWidget()
        self.SOURCE_FIND.setObjectName(u"SOURCE_FIND")
        self.MENU2.addTab(self.SOURCE_FIND, "")
        self.tabWidget.addTab(self.radio, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 803, 26))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.MENU2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.progressBar.setFormat(QCoreApplication.translate("MainWindow", u"%p%", None))
        self.TIME.setText(QCoreApplication.translate("MainWindow", u"TIME: HH:MM:SS", None))
        self.DATE.setText(QCoreApplication.translate("MainWindow", u"DATE: DD/MM/YYYY", None))
        self.radSensorStatus.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.airSensorStatus.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.main), QCoreApplication.translate("MainWindow", u"MAIN", None))
        self.SENS1.setText(QCoreApplication.translate("MainWindow", u"SENSOR 1", None))
        self.SENS2.setText(QCoreApplication.translate("MainWindow", u"SENSOR 2", None))
        self.SENS3.setText(QCoreApplication.translate("MainWindow", u"SENSOR 3", None))
        self.SENS4.setText(QCoreApplication.translate("MainWindow", u"SENSOR 4", None))
        self.SENS5.setText(QCoreApplication.translate("MainWindow", u"SENSOR 5", None))
        self.SENS6.setText(QCoreApplication.translate("MainWindow", u"SENSOR 6", None))
        self.SENS7.setText(QCoreApplication.translate("MainWindow", u"SENSOR 7", None))
        self.SENS8.setText(QCoreApplication.translate("MainWindow", u"SENSOR 8", None))
        self.TEMP.setText(QCoreApplication.translate("MainWindow", u"TEMPERATURE: fff deg", None))
        self.SENSGRAPH.setText(QCoreApplication.translate("MainWindow", u"GRAPH", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.air), QCoreApplication.translate("MainWindow", u"AIR", None))
        self.sec4.setText(QCoreApplication.translate("MainWindow", u"4 SEC AVG", None))
        self.min.setText(QCoreApplication.translate("MainWindow", u"1 MIN AVG", None))
        self.hour.setText(QCoreApplication.translate("MainWindow", u"1 HOUR AVG", None))
        self.hour24.setText(QCoreApplication.translate("MainWindow", u"24 HOUR AVG", None))
        self.lifetime.setText(QCoreApplication.translate("MainWindow", u"LIFETIME S", None))
        self.SELGRAPHRAD.setText(QCoreApplication.translate("MainWindow", u"GRAPH", None))
        self.sel_4.setText(QCoreApplication.translate("MainWindow", u"4 SEC AVG", None))
        self.sel_1min.setText(QCoreApplication.translate("MainWindow", u"1 MIN AVG", None))
        self.sel_1hour.setText(QCoreApplication.translate("MainWindow", u"1 HOUR AVG", None))
        self.sel_24h.setText(QCoreApplication.translate("MainWindow", u"24 HOUR AVG", None))
        self.sel_life.setText(QCoreApplication.translate("MainWindow", u"LIFETIME S", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.rad), QCoreApplication.translate("MainWindow", u"RAD", None))
        self.OSM.setText(QCoreApplication.translate("MainWindow", u"OSM", None))
        self.TERRAIN.setText(QCoreApplication.translate("MainWindow", u"TERRAIN", None))
        self.HILL.setText(QCoreApplication.translate("MainWindow", u"HILL MAP", None))
        self.MAP.setText(QCoreApplication.translate("MainWindow", u"MAP PLACEHOLDER", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.map), QCoreApplication.translate("MainWindow", u"MAP", None))
        self.FREQ.setText(QCoreApplication.translate("MainWindow", u"FREQUENCY: ###.### MHz", None))
        self.FREQ_GRAPH.setText(QCoreApplication.translate("MainWindow", u"FREQUENCY GRAPH PLACE-HOLDER", None))
        self.MENU2.setTabText(self.MENU2.indexOf(self.RADIO), QCoreApplication.translate("MainWindow", u"RADIO", None))
        self.MENU2.setTabText(self.MENU2.indexOf(self.SOURCE_FIND), QCoreApplication.translate("MainWindow", u"SOURCE FINDER", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.radio), QCoreApplication.translate("MainWindow", u"RADIO", None))
    # retranslateUi

