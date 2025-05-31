#!/usr/bin/env python3
# database.py

import sqlite3
import datetime

# Define the database file
DATABASE_FILE = 'sensors.db'

def create_connection():
    """
    Create and return a database connection to the SQLite database.
    """
    return sqlite3.connect(DATABASE_FILE)

def init_db():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
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
    Returns:
      List of tuples [(timestamp_str, s1, s2, s3, s4, lat, lon), …]
      for rows in the last `minutes` minutes.
    """
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)) \
               .isoformat(sep=' ')
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
      SELECT timestamp, sensor1, sensor2, sensor3, sensor4, latitude, longitude
      FROM sensor_data
      WHERE timestamp >= ?
      ORDER BY timestamp ASC
    ''', (cutoff,))
    rows = cur.fetchall()
    conn.close()
    return rows

def query_recent_gps(minutes=60):
    """
    Returns:
      [[lat, lon], …] for the last `minutes` minutes.
    """
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
      SELECT latitude, longitude
      FROM sensor_data
      WHERE timestamp >= datetime('now', ?)
      ORDER BY timestamp ASC
    ''', (f'-{minutes} minutes',))
    rows = cur.fetchall()
    conn.close()
    return [list(r) for r in rows]

# if __name__ == '__main__':
#     # For testing: Initialize the database and insert a sample record.
#     init_db()
#     insert_sensor_data(23.4, 45.6, 12.3, 78.9, 40.7128, -74.0060)
#     # Print all sensor data from the last 10 minutes.
#     for row in query_recent_data(10):
#         print(row)
