import smbus
import time
import os

ADDR = 0x2d
LOW_VOL = 3150 #mV

low = 0
bus = smbus.SMBus(1)
while True:
    data = bus.read_i2c_block_data(ADDR, 0x02, 0x01)
    if(data[0] & 0x40):
        print("Fast Charging state")
    elif(data[0] & 0x80):
        print("Charging state")
    elif(data[0] & 0x20):
        print("Discharge state")
    else:
        print("Idle state")
        
    data = bus.read_i2c_block_data(ADDR, 0x10, 0x06)
    print("VBUS Voltage %5dmV"%(data[0] | data[1] << 8))
    print("VBUS Current %5dmA"%(data[2] | data[3] << 8))
    print("VBUS Power   %5dmW"%(data[4] | data[5] << 8))
        
    data = bus.read_i2c_block_data(ADDR, 0x20, 0x0C)
    print("Battery Voltage %d mV"%(data[0] | data[1] << 8))
    current = (data[2] | data[3] << 8)
    if(current > 0x7FFF):
        current -= 0xFFFF
    print("Battery Current %d mA"%current)
    print("Battery Percent %d%%"%(int(data[4] | data[5] << 8)))
    print("Remaining Capacity %d mAh"%(data[6] | data[7] << 8))
    if(current < 0):
        print("Run Time To Empty %d min"%(data[8] | data[9] << 8))
    else:
        print("Average Time To Full %d min"%(data[10] | data[11] << 8))

    data = bus.read_i2c_block_data(ADDR, 0x30, 0x08)
    V1 = (data[0] | data[1] << 8)
    V2 = (data[2] | data[3] << 8)
    V3 = (data[4] | data[5] << 8)
    V4 = (data[6] | data[7] << 8)
    print("Cell Voltage1 %d mV"%V1)
    print("Cell Voltage2 %d mV"%V2)
    print("Cell Voltage3 %d mV"%V3)
    print("Cell Voltage4 %d mV"%V4)
    
    if(((V1 < LOW_VOL) or (V2 < LOW_VOL) or (V3 < LOW_VOL) or (V4 < LOW_VOL)) and (current < 50)):
        low += 1
        if(low >= 30):
            print("System shutdown now")
            address = os.popen("i2cdetect -y -r 1 0x2d 0x2d | egrep '2d' | awk '{print $2}'").read()
            if(address!='2d\n'):
                print("0x2d i2c address not detected, something wrong.")
            else:
                print("If charged, the system can be powered on again")
                # write 0x55 to 0x01 register of 0x2d Address device
                os.popen("i2cset -y 1 0x2d 0x01 0x55")
            os.system("sudo poweroff")
        else:
            print("Voltage Low,please charge in time,otherwise it will shut down in {:2d} s".format(60-2*low))
    else:
        low = 0
        
    print("")
    time.sleep(2)