import pygame
import sys
from datetime import datetime

#Initial Variables
resol = (800, 600) #sets resolution
current = datetime.now()
clock = pygame.time.Clock() #Clock manages how fast the screen updates

#This program as 06/18/2024 was initially built verbatim by ChatGPT 4, has been worked on and improved over time by the stated author.
#Initialize Pygame
pygame.init()
lastUpdate = pygame.time.get_ticks() #To check how much time has passed

#Set up the display
screen = pygame.display.set_mode(resol) #Adust resolution to fit your display
pygame.display.set_caption('Pip-Boy Hand-Held Environment Monitor') #Sets Window caption

#Setting up Font
font = pygame.font.Font(None, 50) #Sets Text Font, default font, size 36
fontS = pygame.font.Font(None, 32)

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

    #Draw Screen
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)
    screen.blit(text3, text_rect3)
    screen.blit(text4, text_rect4)
    screen.blit(text5, text_rect5)
    

def main_screen(screen):
    #main screen content
    #Background Image
    screen.fill((0, 0, 0)) #Fill screen with blanking
    screen1 = pygame.image.load(r'C:\Users\marc\OneDrive\Desktop\Projects Remote\Raspberry Pi projects\PipBoy\VaultBoy2fill.png') #Image location to show on the screen
    screen1_rect = screen1.get_rect() #Gets image width/height information
    screen1_resi = pygame.transform.scale(screen1, (500, 500)) #Resizes image
    screen.fill((0, 0, 0)) #Fill screen with blanking color to essentially refresh the screen
    screen.blit(screen1_resi, (150, 75))    #This function takes a pygame surface (some "image" data) and displays it on top of everything before it, requires arguments, (the image data, the coordinates

    #delete once find answer
    ############
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

    #Draw Screen
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)
    screen.blit(text3, text_rect3)
    screen.blit(text4, text_rect4)
    screen.blit(text5, text_rect5)
    #################
    #delete once find answer

    #Update Sensor Values Here
    current = datetime.now()    #Runs the datetime function, getting the exact time and date from the system clock, as its in the looping structure it updates every tick
    sec = current.second        #Grabs the second data from the datetime function
    minute = current.minute     #Grabs the minute data from the datetime function
    hour = current.hour         #Grabs the hour data from the datetime function

    #bootstraps() #Why wont this work

    #Time
    textTime = font.render(f'Time: {hour}:{minute}:{sec}', True, (0, 142, 0))
    textTime_rect = textTime.get_rect()
    textTime_rect.center = (150, 550)
    screen.blit(textTime, textTime_rect)

    #Date
    month = current.month       #Grabs the month data from the datetime function
    day = current.day           #Grabs the day data from the date time function
    year = current.year         #Grabs the year data from the date time function
    datetext = font.render(f'{month}/{day}/{year}', True, (0, 142, 0))
    datetext_rect = datetext.get_rect()
    datetext_rect.center = (650, 550)
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

    #delete once find answer
    ############
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

    #Draw Screen
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)
    screen.blit(text3, text_rect3)
    screen.blit(text4, text_rect4)
    screen.blit(text5, text_rect5)
    #################
    #delete once find answer

    #Temp
    temp = fontS.render(f'Temp: {tempsens}', True, (0, 142, 0))
    temp_rect = temp.get_rect()
    temp_rect.topleft = (50, 150) #Places the topleft portion of the box at these x,y coordinates

    #Humidity
    humid = fontS.render(f'Humidity: {humidsens}', True, (0, 142, 0))
    humid_rect = humid.get_rect()
    humid_rect.topleft =(50, 250)

    #CO%
    COper = fontS.render(f'CO: {COsens}', True, (0, 142, 0))
    CO_rect = COper.get_rect()
    CO_rect.topleft = (50, 350)

    #CO2%
    CO2per = fontS.render(f'CO2: {CO2sens}', True, (0, 142, 0))
    CO2_rect = CO2per.get_rect()
    CO2_rect.topleft = (50, 450)

    #O2%
    O2per = fontS.render(f'O2: {O2sens}', True, (0, 142, 0))
    O2_rect = O2per.get_rect()
    O2_rect.topleft = (50, 550)

    #VOC
    VOCper = fontS.render(f'VOC: {VOCsens}', True, (0, 142, 0))
    VOC_rect = VOCper.get_rect()
    #VOC_rect.center = (600, 150) #Centers the coordinates of the box at these x,y coordinates
    VOC_rect.topleft = (600,150)

    #Air Quality Warning Box

    #VOC Explosion Risk Warning Box

    screen.blit(temp, temp_rect)
    screen.blit(humid, humid_rect)
    screen.blit(COper, CO_rect)
    screen.blit(CO2per, CO2_rect)
    screen.blit(O2per, O2_rect)
    screen.blit(VOCper, VOC_rect)



#Main Loop
running = True
clock.tick(1) #Limits to 30 frames per second
current_screen = main_screen
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                current_screen = air_screen if current_screen == main_screen else main_screen
    
    now = pygame.time.get_ticks() #get current time

    #Update the display
    current_screen(screen)
    pygame.display.flip()


#Clean up and exit
pygame.quit()
sys.exit()