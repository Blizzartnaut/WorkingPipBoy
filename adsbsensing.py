import requests
import json

def poll_adsb_data():
    """
    Poll the dump1090 JSON endpoint and return a list of aircraft data.
    Each aircraft entry is a dictionary containing keys such as 'lat', 'lon', 'track', etc.
    """
    try:
        response = requests.get("http://localhost:8080", timeout=2)
        if response.status_code == 200:
            data = response.json()
            # The JSON structure typically has an "aircraft" key with a list of aircraft dictionaries.
            return data.get("aircraft", [])
    except Exception as e:
        print("Error polling ADS-B data:", e)
    return []