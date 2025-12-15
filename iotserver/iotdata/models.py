# app_name/models.py

from django.db import models

# --- ARDUINO DATA MODEL ---
class ArduinoData(models.Model):
    # NEW: Unique identifier for the sensor board (e.g., ARDU_01)
    sensor_id = models.CharField(max_length=10, default='ARDU_01')
    
    # NEW: The time the data was captured by the NodeMCU (from NTP). 
    # NOTE: The incoming JSON field is named 'timestamp'.
    device_capture_time = models.TimeField(blank=True, null=True) 
    
    # Sensor Readings
    ir1 = models.IntegerField(default=0)
    ir2 = models.IntegerField(default=0)
    piezo = models.FloatField(default=0.0)
    speed = models.FloatField(default=0.0)
    
    # Relay States
    arduino_relay = models.BooleanField(default=False)
    piezo_relay = models.BooleanField(default=False)
    
    # Server Receive Time (Automatically set)
    server_receive_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Arduino Data | Speed: {self.speed} km/h"

# --- NODEMCU DATA MODEL ---
class NodeMCUData(models.Model):
    # NEW: Unique identifier for the sensor board (e.g., NMCU_01)
    sensor_id = models.CharField(max_length=10, default='NMCU_01')
    
    # NEW: The time the data was captured by the NodeMCU (from NTP). 
    device_capture_time = models.TimeField(blank=True, null=True)
    
    # Sensor Readings
    ir1 = models.IntegerField(default=0)
    ir2 = models.IntegerField(default=0)
    
    # Relay State
    nodemcu_relay = models.BooleanField(default=False)
    
    # Server Receive Time (Automatically set)
    server_receive_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NodeMCU Data | IR1: {self.ir1}"