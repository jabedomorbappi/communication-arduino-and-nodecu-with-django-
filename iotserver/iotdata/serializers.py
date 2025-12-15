# iotdata/serializers.py
from rest_framework import serializers
from .models import ArduinoData, NodeMCUData

class ArduinoDataSerializer(serializers.ModelSerializer):
    device_capture_time = serializers.TimeField(
        input_formats=['%H:%M:%S'],  # Accepts "11:08:47" from NTP
        required=False,
        allow_null=True
    )

    class Meta:
        model = ArduinoData
        fields = (
            'sensor_id', 'device_capture_time',
            'ir1', 'ir2', 'piezo', 'speed',
            'arduino_relay', 'piezo_relay'
        )

class NodeMCUDataSerializer(serializers.ModelSerializer):
    device_capture_time = serializers.TimeField(
        input_formats=['%H:%M:%S'],
        required=False,
        allow_null=True
    )

    class Meta:
        model = NodeMCUData
        fields = (
            'sensor_id', 'device_capture_time',
            'ir1', 'ir2', 'nodemcu_relay'
        )