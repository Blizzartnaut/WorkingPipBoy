import serial
import datetime
import subprocess

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

    utc_time_str = parts[1]
    date_str = parts[9]

    try:
        # Parse the UTC time
        hour = int(utc_time_str[0:2])
        minute = int(utc_time_str[2:4])
        second = int(utc_time_str[4:6])
        
        # Parse the date; assume date_str is DDMMYY and year is 2000+
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:6]) + 2000
        
        # Create a datetime object in UTC
        utc_dt = datetime.datetime(year, month, day, hour, minute, second)
        print("UTC time from GPS:", utc_dt)
        
        # Convert to Eastern Standard Time (UTC-5)
        est_dt = utc_dt - datetime.timedelta(hours=5)
        print("Converted to EST:", est_dt)
        
        # Format the new time as required by the date command (e.g., "YYYY-MM-DD HH:MM:SS")
        new_time_str = est_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Set system time (requires sudo privileges)
        print("Setting system time to:", new_time_str)
        subprocess.run(['sudo', 'date', '-s', new_time_str])
        subprocess.run('sudo fake-hwclock save')
    except Exception as e:
        print("Error parsing time:", e)

    return latitude, longitude,



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
