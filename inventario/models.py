from django.db import models
from decimal import Decimal, ROUND_HALF_UP

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=5, unique=True, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    precio_dolar = models.DecimalField(max_digits=10, decimal_places=2)
    precio_bs = models.DecimalField(max_digits=15, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True, null=True)
    porcentaje_ganancia = models.DecimalField(max_digits=5, decimal_places=2, default=0) # Permite hasta 999.99%
    precio_individual_dolar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_individual_bs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        # Redondear a 2 decimales antes de guardar
        if self.precio_dolar is not None:
            self.precio_dolar = Decimal(self.precio_dolar).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.precio_bs is not None:
            self.precio_bs = Decimal(self.precio_bs).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.stock is None:
            self.stock = Decimal('0.00')
        else:
            self.stock = Decimal(self.stock).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.precio_individual_dolar is not None:
            self.precio_individual_dolar = Decimal(self.precio_individual_dolar).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.precio_individual_bs is not None:
            self.precio_individual_bs = Decimal(self.precio_individual_bs).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.porcentaje_ganancia is not None:
            self.porcentaje_ganancia = Decimal(self.porcentaje_ganancia).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if not self.codigo:
            last = Producto.objects.all().order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.codigo = str(next_id).zfill(5)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"