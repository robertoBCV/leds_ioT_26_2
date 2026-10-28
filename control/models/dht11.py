from django.db import models


class SensorDht11(models.Model):
    nombre = models.CharField( max_length=50  )
    codigo = models.CharField(max_length=20,unique=True)
    pin = models.PositiveIntegerField()
    temperatura = models.FloatField(default=0)
    humedad = models.FloatField(default=0 )
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class LecturaDht11(models.Model):
    sensor = models.ForeignKey(SensorDht11,on_delete=models.CASCADE,related_name="lecturas")
    temperatura = models.FloatField()
    humedad = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True )

    class Meta:
        ordering = ["-fecha"]