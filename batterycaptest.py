import smbus2
import time

# Set your device parameters (adjust as necessary)
DEVICE_BUS = 1
DEVICE_ADDR = 0x17  # This is the address used in the demo code

# Create the bus instance (you may want to create this once and reuse it)
bus = smbus2.SMBus(DEVICE_BUS)

def get_remaining_capacity():
    """
    Reads data from the UPS HAT registers and returns the remaining battery capacity as a percentage.
    
    This function reads registers 1 through 254 (as in the demo code) into a buffer,
    then computes the battery remaining capacity using the values at indices 19 and 20.
    """
    aReceiveBuf = []
    # The demo code uses a dummy value at index 0
    aReceiveBuf.append(0x00)  # Placeholder for index 0

    # Read registers 1 to 254 from the UPS device.
    # (This is what the demo code does; you might optimize this to read only the needed registers.)
    for i in range(1, 255):
        try:
            byte_value = bus.read_byte_data(DEVICE_ADDR, i)
            aReceiveBuf.append(byte_value)
        except Exception as e:
            print(f"Error reading register {i}: {e}")
            # Append a default value in case of error to keep the indices in place.
            aReceiveBuf.append(0)

    # Compute remaining capacity:
    # Note: aReceiveBuf[19] corresponds to the lower byte and [20] to the upper byte.
    remaining_capacity = (aReceiveBuf[20] << 8) | aReceiveBuf[19]
    return remaining_capacity

# Test the function
if __name__ == "__main__":
    capacity = get_remaining_capacity()
    print(f"Battery remaining capacity: {capacity}%")
