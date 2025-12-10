# from django.db import models

# class VehicleData(models.Model):
#     device = models.CharField(max_length=50)
#     ir1 = models.IntegerField()
#     ir2 = models.IntegerField()
#     piezo = models.FloatField(default=0)
#     relay = models.BooleanField()
#     speed = models.FloatField()
#     timestamp = models.DateTimeField(auto_now_add=True)
#     # ADD THIS LINE → tracks last update time
#     last_seen = models.DateTimeField(auto_now=True)   # ← THIS IS THE KEY!


#     def __str__(self):
#         return f"{self.device} | {self.timestamp}"


from django.db import models

class ArduinoData(models.Model):
    ir1 = models.IntegerField(default=0)
    ir2 = models.IntegerField(default=0)
    piezo = models.FloatField(default=0.0)
    speed = models.FloatField(default=0.0)
    arduino_relay = models.BooleanField(default=False)
    piezo_relay = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class NodeMCUData(models.Model):
    ir1 = models.IntegerField(default=0)
    ir2 = models.IntegerField(default=0)
    nodemcu_relay = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)