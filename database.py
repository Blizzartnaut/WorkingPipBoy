#!/usr/bin/env python3
# database.py

import sqlite3

# Define the database file
DATABASE_FILE = 'sensors.db'

def create_connection():
    """
    Create and return a database connection to the SQLite database.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def init_db():
    """
    Initialize the database by creating the sensor_data table if it does not exist.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sensor1 REAL,
            sensor2 REAL,
            sensor3 REAL,
            sensor4 REAL,
            latitude REAL,
            longitude REAL
        )
    ''')
    conn.commit()
    conn.close()

def insert_sensor_data(sensor1, sensor2, sensor3, sensor4, latitude, longitude):
    """
    Insert a new row of sensor data into the sensor_data table.

    Parameters:
      sensor1, sensor2, sensor3, sensor4 (float): Sensor readings.
      latitude, longitude (float): GPS coordinates.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_data (sensor1, sensor2, sensor3, sensor4, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sensor1, sensor2, sensor3, sensor4, latitude, longitude))
    conn.commit()
    conn.close()

def query_recent_data(minutes=10):
    """
    Query sensor data from the last `minutes` minutes.

    Parameters:
      minutes (int): The number of minutes in the past from which to query data.

    Returns:
      List of rows (tuples) from the sensor_data table.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sensor_data 
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    ''', (f'-{minutes} minutes',))
    rows = cursor.fetchall()
    conn.close()
    return rows

def query_recent_gps(minutes=60):
    """
    Query GPS coordinates from the last `minutes` minutes.
    
    Returns:
      A list of [latitude, longitude] pairs.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT latitude, longitude FROM sensor_data 
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    ''', (f'-{minutes} minutes',))
    rows = cursor.fetchall()
    conn.close()
    # rows is a list of tuples; convert to list of lists if needed
    return [list(row) for row in rows]

# if __name__ == '__main__':
#     # For testing: Initialize the database and insert a sample record.
#     init_db()
#     insert_sensor_data(23.4, 45.6, 12.3, 78.9, 40.7128, -74.0060)
#     # Print all sensor data from the last 10 minutes.
#     for row in query_recent_data(10):
#         print(row)
