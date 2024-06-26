import pygame
import sys
from datetime import datetime
import os
import RPi.GPIO as GPIO
import time
from collections import deque
from threading import Timer
from osgeo import gdal, osr
import matplotlib.pyplot as plt
import pynmea2

#NEED TO FIX TIMER ISSUE BEFORE NEXT COMMIT

#GPIO Pin Set up
clk = 17 #Variable set at pin location
dt = 18
button = 27
radPin = 15
radlight = 5 #Lights up a light every time the gieger counter measures a count

#GPIO Setup
GPIO.setmode(GPIO.BCM) #Board Control Module?
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Sets up a pin, input, active high
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(radPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Sets up a pin, input, active low
#GPIO.setup(radlight, GPIO.OUT, )

#Initial Variables
dir_path = os.path.dirname(os.path.realpath(__file__)) #This function creates a relational path to the object.
resol = (800, 480) #sets resolution
current = datetime.now()
clock = pygame.time.Clock() #Clock manages how fast the screen updates
counter = 0 #Used for counting from zero
clkLstSt = GPIO.input(clk) #Checks last state of clk pin
conv = 0.008120370 #Conversion factor from counts to Sieverts per minute
global counts
global sv
global minCounts
global hourCounts
global hourSv
global dayCounts
global totalCounts
global changeCount
global lifeSv
global menuRects

counts = 0
sv = 0
daycounts = 0
hourSv = 0
changeCount = 0
minCounts = deque(maxlen = 60)
hourCounts = deque(maxlen = 1440)
totalCounts = 0
lifeSv = 0
menuRects = {}

#This program as 06/18/2024 was initially built verbatim by ChatGPT 4, has been worked on and improved over time by the stated author.
#Initialize Pygame
pygame.init()
image_path = os.path.join(dir_path, 'VaultBoy2fill.png')
lastUpdate = pygame.time.get_ticks() #To check how much time has passed

#Set up the display
screen = pygame.display.set_mode((resol), pygame.FULLSCREEN) #Adust resolution to native #Do not test on home machine
#screen = pygame.display.set_mode(resol) #REMOVE BEFORE PUSH, TESTING
pygame.display.set_caption('Pip-Boy Hand-Held Environment Monitor') #Sets Window caption

#Setting up Font
font = pygame.font.Font(None, 50) #Sets Text Font, default font, size 36
fontS = pygame.font.Font(None, 32)
fontW = pygame.font.Font(None, 75)

#Radiation Counters
def handle_interrupt(channel):
    global totalCounts
    totalCounts += 1

#Load map file so it can be displayed
def load_displaymap(filepath):
    # Load geospatial raster file and display it using matplotlib.
    dataset = gdal.Open(filepath)
    band = dataset.GetRasterBand(1)
    arr = band.ReadAsArrary()

    plt.imshow(arr, cmap="gray")
    plt.show()

#GPIO.add_event_detect(radPin, GPIO.RISING, callback=handle_interrupt) #This line is crashing the script for some reason, INVESTIGATE

def calculate_sieverts():
    #Run every 60 seconds
    counts = sum(minCounts) #Sum of all counts in the last minute
    sv = counts * conv #Convert counts per minute to Sieverts

    #Update Rolling Counts
    minCounts.append(counts)
    if len(minCounts) == 60:
        hourSum = sum(minCounts)
        hourCounts.append(hourSum)
        hourSv = hourSum * conv #Converts the hour counts to sieverts
        minCounts.clear() #Reset minute counts

    #Repeat every minute
    Timer(60, calculate_sieverts).start()

def lifetime_sieverts():
    #Run every 60 seconds
    lifeSv = totalCounts * conv
    Timer(60, lifetime_sieverts).start()

def monitor_environment():
    #Run every 4 seconds to check for rapid changes
    startCount = totalCounts
    time.sleep(4)
    endCount = totalCounts
    changeCount = endCount - startCount
    Timer(4, monitor_environment).start()

def bootstraps(): #Why wont this work?
    #Main
    text1 = font.render("MAIN", True, (0, 142, 0)) #Text, anti-aliasign, color (RBG)
    text_rect1 = text1.get_rect()
    text_rect1.center = (80, 45)

    #Air
    text2 = font.render("AIR", True, (0, 142, 0)) #Text, anti-aliasign, color (RBG)
    text_rect2 = text2.get_rect()
    text_rect2.center = (240, 45)

    #Rad
    text3 = font.render("RAD", True, (0, 142, 0)) #Text, anti-aliasign, color (RBG)
    text_rect3 = text3.get_rect()
    text_rect3.center = (400, 45)

    #Map
    text4 = font.render("MAP", True, (0, 142, 0)) #Text, anti-aliasign, color (RBG)
    text_rect4 = text4.get_rect()
    text_rect4.center = (560, 45)

    #Radio
    text5 = font.render("RADIO", True, (0, 142, 0)) #Text, anti-aliasign, color (RBG)
    text_rect5 = text5.get_rect()
    text_rect5.center = (720, 45)

    menuRects = {
    0: text_rect1, 
    1: text_rect2,
    2: text_rect3,
    3: text_rect4,
    4: text_rect5,
    #Gets Menu surface data
}

    return text1, text2, text3, text4, text5, text_rect1, text_rect2, text_rect3, text_rect4, text_rect5

global hed
hed = bootstraps()

def main_screen(screen):
    #main screen content
    #Background Image
    screen.fill((0, 0, 0)) #Fill screen with blanking
    screen1 = pygame.image.load('VaultBoy2fill.png') #Image location to show on the screen
    screen1_rect = screen1.get_rect() #Gets image width/height information
    screen1_resi = pygame.transform.scale(screen1, (500, 500)) #Resizes image
    screen.fill((0, 0, 0)) #Fill screen with blanking color to essentially refresh the screen
    screen.blit(screen1_resi, (150, 75))    #This function takes a pygame surface (some "image" data) and displays it on top of everything before it, requires arguments, (the image data, the coordinates

    #Draw Screen
    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])

    #Update Sensor Values Here
    current = datetime.now()    #Runs the datetime function, getting the exact time and date from the system clock, as its in the looping structure it updates every tick
    sec = current.second        #Grabs the second data from the datetime function
    minute = current.minute     #Grabs the minute data from the datetime function
    hour = current.hour         #Grabs the hour data from the datetime function

    #bootstraps() #Why wont this work

    #Time
    textTime = font.render(f'Time: {hour}:{minute}:{sec}', True, (0, 142, 0))
    textTime_rect = textTime.get_rect()
    textTime_rect.center = (150, 440)
    screen.blit(textTime, textTime_rect)

    #Date
    month = current.month       #Grabs the month data from the datetime function
    day = current.day           #Grabs the day data from the date time function
    year = current.year         #Grabs the year data from the date time function
    datetext = font.render(f'{month}/{day}/{year}', True, (0, 142, 0))
    datetext_rect = datetext.get_rect()
    datetext_rect.center = (650, 440)
    screen.blit(datetext, datetext_rect)

def air_screen(screen):
    #air quality sensor screen content
    #Update Sensor Values Here
    screen.fill((0, 0, 0)) #Fill screen with blanking

    #Temperorary Sensor data for testing
    tempsens = 73.4
    humidsens = 46.2
    COsens = 0.36
    CO2sens = 3.6
    O2sens = 19.4
    VOCsens = 0.01

    #Draw Screen
    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])

    #Temp
    temp = fontS.render(f'Temp: {tempsens}', True, (0, 142, 0))
    temp_rect = temp.get_rect()
    temp_rect.topleft = (50, 145) #Places the topleft portion of the box at these x,y coordinates

    #Humidity
    humid = fontS.render(f'Humidity: {humidsens}', True, (0, 142, 0))
    humid_rect = humid.get_rect()
    humid_rect.topleft =(50, 210)

    #CO%
    COper = fontS.render(f'CO: {COsens}', True, (0, 142, 0))
    CO_rect = COper.get_rect()
    CO_rect.topleft = (50, 275)

    #CO2%
    CO2per = fontS.render(f'CO2: {CO2sens}', True, (0, 142, 0))
    CO2_rect = CO2per.get_rect()
    CO2_rect.topleft = (50, 340)

    #O2%
    O2per = fontS.render(f'O2: {O2sens}', True, (0, 142, 0))
    O2_rect = O2per.get_rect()
    O2_rect.topleft = (50, 405)

    #VOC
    VOCper = fontS.render(f'VOC: {VOCsens}', True, (0, 142, 0))
    VOC_rect = VOCper.get_rect()
    #VOC_rect.center = (600, 150) #Centers the coordinates of the box at these x,y coordinates
    VOC_rect.topleft = (600, 145)

    #Air Quality Warning Box

    #VOC Explosion Risk Warning Box

    screen.blit(temp, temp_rect)
    screen.blit(humid, humid_rect)
    screen.blit(COper, CO_rect)
    screen.blit(CO2per, CO2_rect)
    screen.blit(O2per, O2_rect)
    screen.blit(VOCper, VOC_rect)

    #Draw Screen
    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])

def rad_screen(screen):
    
    screen.fill((0, 0, 0)) #Fill screen with blanking

    #Draw Screen
    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])

    rad4 = changeCount
    rad60 = sv
    rad1 = hourSv
    rad24 = hourCounts
    radlif = lifeSv

    #Rad Level 4 second
    rad4txt = fontS.render(f'4 Second Average Counts: {rad4}', True, (0, 142, 0))
    rad4txt_rect = rad4txt.get_rect()
    rad4txt_rect.topleft = (600, 145)

    #Rad Level 60 second
    rad60txt = fontS.render(f'60 Second Average: {rad60} Sv', True, (0, 142, 0))
    rad60txt_rect = rad60txt.get_rect()
    rad60txt_rect.topleft = (600, 210)

    #Rad Level 1 hour
    rad1txt = fontS.render(f'Last Hour Average: {rad1} Sv', True, (0, 142, 0))
    rad1txt_rect = rad1txt.get_rect()
    rad1txt_rect.topleft = (50, 145)

    #Rad Level 24 Hour
    rad24txt = fontS.render(f'Last 24 Hours Average: {rad24} Sv', True, (0, 142, 0))
    rad24txt_rect = rad24txt.get_rect()
    rad24txt_rect.topleft = (50, 210)

    #Rad Level Life
    radliftxt = fontS.render(f'Lifetime Exposure: {radlif} Sv', True, (0, 142, 0))
    radliftxt_rect = radliftxt.get_rect()
    radliftxt_rect.topleft = (50, 405)

    screen.blit(rad4txt, rad4txt_rect)
    screen.blit(rad60txt, rad60txt_rect)
    screen.blit(rad1txt, rad1txt_rect)
    screen.blit(rad24txt, rad24txt_rect)
    screen.blit(radliftxt, radliftxt_rect)
    

def map_screen(screen):

    screen.fill((0, 0, 0)) #Fill screen with blanking

    #Draw Screen
    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])
    #WIP
    WIPi = fontW.render("W I P", True, (0, 142, 0))
    WIP_rect = WIPi.get_rect()
    WIP_rect.center = (400, 240)
    screen.blit(WIPi, WIP_rect)

def radio_screen(screen):

    screen.fill((0, 0, 0)) #Fill screen with blanking

    screen.blit(hed[0], hed[5])
    screen.blit(hed[1], hed[6])
    screen.blit(hed[2], hed[7])
    screen.blit(hed[3], hed[8])
    screen.blit(hed[4], hed[9])

    #WIP
    WIPi = font.render("I LOVE YOU KEITH", True, (0, 142, 0))
    WIP_rect = WIPi.get_rect()
    WIP_rect.center = (400, 240)
    screen.blit(WIPi, WIP_rect)

def update_counter():
    global counter
    clkSt = GPIO.input(clk)
    dtSt = GPIO.input(dt)
    if clkSt != clkLstSt:
        if dtSt != clkSt:
            counter += 1
        else:
            counter -= 1
    
        if counter >= 5:
            counter = 0
        elif counter < 0:
            counter = 4
    return counter

#Loop Variables
counter = 0
clkLstSt = GPIO.input(clk)

#Main Loop
running = True
clock.tick(1) #Limits to 30 frames per second
current_screen = main_screen
while running:

    Timer(60, calculate_sieverts).start()
    Timer(4, monitor_environment).start()

    update_counter()

    print("Counter: {}".format(counter))
    #print(f"clkst={clkSt}, dtst={dtSt}, counter={counter}") #prints the status for debugging
    clkLstSt = GPIO.input(clk)
    time.sleep(0.1) #Debouncing with software delay

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     #Check if touchscreen click is within any of menu rects
        #     pos = pygame.mouse.get_pos() #Checks position of click and returns value
        #     if pos ==  #Check if position matches any values within the menu rects, and if so set the "Counter" to that screen detail
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                counter += 1
            elif event.key == pygame.K_LEFT:
                counter -= 1

            if counter >= 5:
                counter = 0
            elif counter < 0:
                counter = 4

    #Update Screen Based on counter value        
    if counter == 0:
        current_screen = main_screen
    elif counter == 1:
        current_screen = air_screen
    elif counter == 2:
        current_screen = rad_screen
    elif counter == 3:
        current_screen = map_screen
    elif counter == 4:
        current_screen = radio_screen
    else:
        current_screen = main_screen

    now = pygame.time.get_ticks() #get current time

    #Update the display
    current_screen(screen)
    pygame.display.flip()


#Clean up and exit
pygame.quit()
sys.exit()
GPIO.cleanup()
Timer.join()

#NEED TO FIX TIMER ISSUE