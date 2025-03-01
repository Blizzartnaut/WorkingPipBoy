import smbus
import time
import os

ADDR = 0x2d
LOW_VOL = 3150  # mV

# Initialize the bus once
bus = smbus.SMBus(1)

def get_battery_info():
    info = {}
    try:
        # Read charging state
        data = bus.read_i2c_block_data(ADDR, 0x02, 0x01)
        if data[0] & 0x40:
            info["charging_state"] = "Fast Charging"
        elif data[0] & 0x80:
            info["charging_state"] = "Charging"
        elif data[0] & 0x20:
            info["charging_state"] = "Discharging"
        else:
            info["charging_state"] = "Idle"
        
        # Read VBUS data
        data = bus.read_i2c_block_data(ADDR, 0x10, 0x06)
        info["vbus_voltage"] = (data[0] | data[1] << 8)  # mV
        info["vbus_current"] = (data[2] | data[3] << 8)  # mA
        info["vbus_power"]   = (data[4] | data[5] << 8)  # mW
        
        # Read Battery data
        data = bus.read_i2c_block_data(ADDR, 0x20, 0x0C)
        info["battery_voltage"] = (data[0] | data[1] << 8)  # mV
        current = (data[2] | data[3] << 8)
        if current > 0x7FFF:
            current -= 0xFFFF
        info["battery_current"] = current  # mA
        info["battery_percent"] = int(data[4] | data[5] << 8)
        info["remaining_capacity"] = (data[6] | data[7] << 8)  # mAh
        
        if current < 0:
            info["runtime_empty"] = (data[8] | data[9] << 8)  # min
        else:
            info["time_to_full"] = (data[10] | data[11] << 8)  # min
        
        # Read cell voltages
        data = bus.read_i2c_block_data(ADDR, 0x30, 0x08)
        info["cell_voltage1"] = (data[0] | data[1] << 8)
        info["cell_voltage2"] = (data[2] | data[3] << 8)
        info["cell_voltage3"] = (data[4] | data[5] << 8)
        info["cell_voltage4"] = (data[6] | data[7] << 8)
        
        # Check if any cell is below LOW_VOL and if current is low
        if (((info["cell_voltage1"] < LOW_VOL) or (info["cell_voltage2"] < LOW_VOL) or 
             (info["cell_voltage3"] < LOW_VOL) or (info["cell_voltage4"] < LOW_VOL))
             and (current < 50)):
            info["low_warning"] = True
        else:
            info["low_warning"] = False
        
    except Exception as e:
        info["error"] = str(e)
    
    return info
