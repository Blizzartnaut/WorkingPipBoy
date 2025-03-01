#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import smbus
import time
import logging
import signal
import PyQt5
from PyQt5.QtGui import (
    QIcon,
    QPixmap
)
from PyQt5.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMessageBox
)
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    QTimer,
    QSize
)

signal.signal(signal.SIGINT, signal.SIG_DFL)
logging.basicConfig(format="%(message)s", level=logging.INFO)

ADDR = 0x2d
LOW_VOL = 3150 #mV
bus = smbus.SMBus(1)
        
class Worker(QObject):
    trayMessage = pyqtSignal(list, list, list, list)

    def run(self):
        while True:
            data = bus.read_i2c_block_data(ADDR, 0x02, 0x02)
            list1 = data
            data = bus.read_i2c_block_data(ADDR, 0x10, 0x06)
            list2 = [0,0,0]
            list2[0] = data[0] | data[1] << 8
            list2[1] = data[2] | data[3] << 8
            list2[2] = data[4] | data[5] << 8
            data = bus.read_i2c_block_data(ADDR, 0x20, 0x0C)
            list3 = [0,0,0,0,0,0]
            list3[0] = data[0] | data[1] << 8
            list3[1] = data[2] | data[3] << 8
            list3[2] = data[4] | data[5] << 8
            list3[3] = data[6] | data[7] << 8
            list3[4] = data[8] | data[9] << 8
            list3[5] = data[10] | data[11] << 8
            if(list3[1] > 0x7FFF):
                list3[1] -= 0xFFFF
            data = bus.read_i2c_block_data(ADDR, 0x30, 0x08)
            list4 = [0,0,0,0]
            list4[0] = data[0] | data[1] << 8
            list4[1] = data[2] | data[3] << 8
            list4[2] = data[4] | data[5] << 8
            list4[3] = data[6] | data[7] << 8
            # bus_voltage = 4.00             # voltage on V- (load side)
            # current = 1000                   # current in mA
            self.trayMessage.emit(list1, list2, list3, list4)
            time.sleep(1);
        
class MainWindow(QMessageBox):
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        self.charge = 0
        self.tray_icon = None
        self.msgBox = None
        self.about = None
        self.counter = 0
    
        QMessageBox.__init__(self)
        self.resize(QSize(300, 200))
        self.setWindowTitle("Battery Status")  # Set a title
        
        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("images/battery.png"))

        '''
            Define and add steps to work with the system tray icon
            show - show window
            Status - Status window
            exit - exit from application
        '''
        show_action = QAction("Status", self)
        quit_action = QAction("Exit", self)
        about_action = QAction("About", self)
        show_action.triggered.connect(self.show)
        about_action.triggered.connect(self.show_about)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(about_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self._thread = QThread(self)
        self._worker = Worker()
        self._worker.moveToThread(self._thread)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.started.connect(self._worker.run)
        self._worker.trayMessage.connect(self.refresh)
        self._thread.start()
        self._timer = QTimer(self,timeout=self.on_timeout)
        self._timer.stop()
    
    def on_timeout(self):
        self.counter -= 1
        if(self.counter > 0):  #countdown
            if(self.charge == 1):
                self.msgBox.hide()
                self.msgBox.close()
                self._timer.stop()
                self.msgBox = None
            else:
                self.msgBox.setInformativeText("auto shutdown after " +str(int(self.counter)) + " seconds");
                self.msgBox.show()
        else:                  #timeout
            address = os.popen("i2cdetect -y -r 1 0x2d 0x2d | egrep '2d' | awk '{print $2}'").read()
            if(address=='2d\n'):
                #print("If charged, the system can be powered on again.")
                #write 0x55 to 0x01 register of 0x2d Address device
                os.popen("i2cset -y 1 0x2d 0x01 0x55")
            os.system("sudo poweroff")

    def refresh(self, list1, list2, list3, list4):
        v = list3[0] / 1000   #Battery Voltage
        c = list3[1] / 1000  #Battery Current
        if(c > 0):self.charge = 1
        else:self.charge = 0
        
        p = list3[2]   #Battery Percentage
        img = "images/battery." + str(int(p / 10 + self.charge * 11)) + ".png"
        self.tray_icon.setIcon(QIcon(img))
        self.setIconPixmap(QPixmap(img))
        s = "%d%%  %.1fV  %.2fA" % (p,v,c)
        self.tray_icon.setToolTip(s)
        if(list1[0] & 0x40):
            info1 = "Fast Charging state\n"
        elif(list1[0] & 0x80):
            info1 = "Charging state\n"
        elif(list1[0] & 0x20):
            info1 = "Discharge state\n"
        else:
            info1 = "Idle state\n"
        info2 = "Voltage:    %2.1fV           Capacity:   %dmAh\n" % (v,list3[3])
        info3 = "Current:    %2.2fA          Time To Empty   %d min\n" % (c,list3[4])
        info4 = "Percent:    %4d%%           Time To Full    %d min\n" % (p,list3[5])
        info5 = "Cell V1:     %4dmV        VBUS Voltage   %2.2fV\n" % (list4[0],list2[0]/1000)
        info6 = "Cell V2:     %4dmV        VBUS Current   %1.2fA\n" % (list4[1],list2[1]/1000)
        info7 = "Cell V3:     %4dmV        VBUS Power     %2.1fW\n" % (list4[2],list2[2]/1000)
        info8 = "Cell V4:     %4dmV        " % (list4[3])
        self.setText(info2+info3+info4+info5+info6+info7+info8+info1);
        localTime = time.localtime(time.time())
        logging.info(f"{localTime.tm_year:04d}-{localTime.tm_mon:02d}-{localTime.tm_mday:02d} {localTime.tm_hour:02d}:{localTime.tm_min:02d}:{localTime.tm_sec:02d}  {s}")
        if(((list4[0] < LOW_VOL) or (list4[1] < LOW_VOL) or (list4[2] < LOW_VOL) or (list4[3] < LOW_VOL)) and self.charge == 0):
            if(self.msgBox == None):
                self.counter = 60
                self._timer.start(1000)
                self.msgBox = QMessageBox(QMessageBox.NoIcon,'Battery Warning',"<p><strong>The battery level is below<br>Please connect in the power adapter</strong>")
                self.msgBox.setIconPixmap(QPixmap("images/batteryQ.png"))
                self.msgBox.setInformativeText("auto shutdown after 60 seconds");
                self.msgBox.setStandardButtons(QMessageBox.NoButton);
                self.msgBox.exec()
            
    def show_about(self):
        if(self.about == None):
            self.about = QMessageBox(QMessageBox.NoIcon,'About',"<p><strong>Battery Monitor Demo</strong><p>Version: v1.0<p>It's a battery Display By waveshare\n")
            self.about.setInformativeText("<a href=\"https://www.waveshare.com\">WaveShare Official Website</a>");
            self.about.setIconPixmap(QPixmap("images/logo.png"))
            self.about.setDefaultButton(None)
            self.about.exec()
            self.about = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    mw = MainWindow()
    sys.exit(app.exec_())