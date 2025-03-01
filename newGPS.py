import serial

def read_gnrmc():
    """
    Opens the serial port and waits for a line that starts with "$GNRMC" or "$GPRMC".
    """
    # Open the serial port (make sure the baud rate matches your GPS settings)
    ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)
    while True:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith('$GNRMC') or line.startswith('$GPRMC'):
            return line

def parse_gnrmc(sentence):
    """
    Parses a $GNRMC sentence and returns the latitude and longitude in decimal degrees.
    
    Returns:
        (latitude, longitude) as floats, or (None, None) if parsing fails.
    """
    parts = sentence.split(',')
    # Check if the GPS data is valid: field 2 (index 2) should be 'A'
    if parts[2] != 'A':
        return None, None

    # Parse latitude: ddmm.mmmm
    lat_str = parts[3]
    lat_dir = parts[4]
    if len(lat_str) < 4:
        return None, None
    lat_deg = float(lat_str[:2])
    lat_min = float(lat_str[2:])
    latitude = lat_deg + (lat_min / 60.0)
    if lat_dir.upper() == 'S':
        latitude = -latitude

    # Parse longitude: dddmm.mmmm
    lon_str = parts[5]
    lon_dir = parts[6]
    if len(lon_str) < 5:
        return None, None
    lon_deg = float(lon_str[:3])
    lon_min = float(lon_str[3:])
    longitude = lon_deg + (lon_min / 60.0)
    if lon_dir.upper() == 'W':
        longitude = -longitude

    return latitude, longitude

def get_coordinates_from_serial():
    """
    Reads the serial port for a $GNRMC sentence, parses it, and returns (latitude, longitude).
    """
    sentence = read_gnrmc()
    lat, lon = parse_gnrmc(sentence)
    print(f"Read coordinates: Latitude = {lat}, Longitude = {lon}")
    return lat, lon

# For testing:
if __name__ == "__main__":
    lat, lon = get_coordinates_from_serial()
    print("Latitude:", lat, "Longitude:", lon)
