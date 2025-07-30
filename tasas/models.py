from django.db import models

class TasaBCV(models.Model):
    fecha = models.DateField(unique=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    activa = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Asegurarse de que solo una tasa pueda estar activa a la vez
        # Si la tasa es activa, desactivar las demás tasas activas
        if self.activa:
            # Desactivar todas las tasas activas antes de activar una nueva
            TasaBCV.objects.filter(activa=True).exclude(pk=self.pk).update(activa=False)
        
    def __str__(self):
        return f"Tasa BCV: {self.valor} ({'Activa' if self.activa else 'Inactiva'}) - {self.fecha}"