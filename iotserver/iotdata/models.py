from django.db import models

class VehicleData(models.Model):
    device = models.CharField(max_length=50)
    ir1 = models.IntegerField()
    ir2 = models.IntegerField()
    piezo = models.IntegerField()
    relay = models.BooleanField()
    speed = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.device} | {self.timestamp}"
