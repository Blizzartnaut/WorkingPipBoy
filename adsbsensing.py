import requests
import json

def fetch_adsb_data():
    url = 'http://localhost:8080/data.json'
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        return data  # This is a list of aircraft dictionaries.
    except Exception as e:
        print("Error fetching ADS-B data:", e)
        return []