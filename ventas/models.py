# ventas/models.py
from django.db import models
from decimal import Decimal, ROUND_HALF_UP
from inventario.models import Producto # Importamos el modelo Producto
from tasas.models import TasaBCV # Importamos la TasaBCV
from django.db import transaction # Importamos transaction para operaciones atómicas
from django.conf import settings # Para relacionar la venta con el usuario loggeado

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    cedula_rif = models.CharField(max_length=20, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre', 'apellido']

    def __str__(self):
        # Esta es la parte importante: define cómo se mostrará el cliente
        full_name = f"{self.nombre}"
        if self.apellido:
            full_name += f" {self.apellido}"
        
        if self.cedula_rif:
            return f"{full_name} ({self.cedula_rif})"
        return full_name.strip()

    def get_full_name(self):
        return f"{self.nombre} {self.apellido or ''}".strip()
    
    pass

class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ventas_realizadas')
    total_dolar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_ultimo_pago = models.DateTimeField(null=True, blank=True) #
    
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('PAGO_MOVIL', 'Pago Móvil'),
        ('MIXTO', 'Mixto'),
        ('ZELLE', 'Zelle'),
        ('CRIPTO', 'Cripto'),
        ('OTRO', 'Otro'),
        ('PENDIENTE', 'Pendiente'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO')
    
    ESTADO_VENTA_CHOICES = [
        ('ADEUDADO', 'Adeudado'), # Añadido el estado 'Adeudado'
        ('COMPLETADA', 'Completada'),
        ('ANULADA', 'Anulada'),
        ('DEVOLUCION', 'Devolución'),
        ('PARCIALMENTE_PAGADA', 'Parcialmente Pagada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_VENTA_CHOICES, default='COMPLETADA')
    
    observaciones = models.TextField(blank=True, null=True)
    # Tasa BCV usada al momento de la venta
    tasa_bcv_venta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Obtener la última tasa BCV si no está establecida
        if not self.tasa_bcv_venta:
            try:
                self.tasa_bcv_venta = TasaBCV.objects.latest('fecha').valor
            except TasaBCV.DoesNotExist:
                self.tasa_bcv_venta = Decimal('1.00') # Valor por defecto si no hay tasa
                
        if self.monto_pagado >= self.total_dolar and self.total_dolar > 0:
            self.estado = 'COMPLETADA'
        elif self.monto_pagado > 0 and self.monto_pagado < self.total_dolar:
            self.estado = 'PARCIALMENTE_PAGADA'
        elif self.monto_pagado == 0 and self.total_dolar > 0:
            self.estado = 'ADEUDADO'

        super().save(*args, **kwargs)
        
    @property
    def monto_restante(self):
        return (self.total_dolar - self.monto_pagado).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def tasa_usada(self):
        return self.tasa_bcv_venta if self.tasa_bcv_venta else Decimal('1.00')

    def __str__(self):
        full_name = f"{self.cliente.nombre} {self.cliente.apellido or ''}".strip() if self.cliente else "N/A"
        return f"Venta #{self.id} - Cliente: {full_name} - Total: ${self.total_dolar} - Pagado: ${self.monto_pagado} - Estado: {self.estado}"

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT) # PROTECT para no borrar productos con ventas
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario_dolar = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario_bs = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal_dolar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_bs = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Si es un nuevo ítem o la cantidad ha cambiado
            if self.pk:
                old_cantidad = VentaItem.objects.get(pk=self.pk).cantidad
                stock_change = self.cantidad - old_cantidad
            else:
                old_cantidad = Decimal('0.00')
                stock_change = self.cantidad

            # Actualizar stock del producto
            self.producto.stock -= stock_change
            self.producto.save(update_fields=['stock'])

            # Calcular precios unitarios y subtotales
            self.precio_unitario_dolar = self.producto.precio_individual_dolar.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Asegurarse de que la venta tenga una tasa_bcv_venta para el cálculo
            if not self.venta.tasa_bcv_venta:
                try:
                    self.venta.tasa_bcv_venta = TasaBCV.objects.latest('fecha').valor
                    self.venta.save(update_fields=['tasa_bcv_venta'])
                except TasaBCV.DoesNotExist:
                    self.venta.tasa_bcv_venta = Decimal('1.00')

            self.precio_unitario_bs = (self.precio_unitario_dolar * self.venta.tasa_bcv_venta).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.subtotal_dolar = (self.cantidad * self.precio_unitario_dolar).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.subtotal_bs = (self.cantidad * self.precio_unitario_bs).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            super().save(*args, **kwargs)

            # Después de guardar el VentaItem, recalcular y actualizar los totales de la Venta principal
            self.venta.total_dolar = sum(item.subtotal_dolar for item in self.venta.items.all()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.venta.total_bs = sum(item.subtotal_bs for item in self.venta.items.all()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.venta.save(update_fields=['total_dolar', 'total_bs'])

    # Sobreescribir el método delete para devolver el stock
    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # Antes de eliminar el ítem, devuelve la cantidad al stock del producto
            self.producto.stock += self.cantidad
            self.producto.save(update_fields=['stock'])

            # Almacena una referencia a la venta antes de eliminar el ítem
            venta_instance = self.venta
            
            super().delete(*args, **kwargs) # Eliminar el VentaItem

            # Después de eliminar, recalcular y actualizar los totales de la Venta principal
            # Asegúrate de que la instancia de venta aún exista (no fue eliminada en cascada)
            if venta_instance: # Esto previene errores si la venta padre también fue eliminada
                venta_instance.total_dolar = sum(item.subtotal_dolar for item in venta_instance.items.all()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                venta_instance.total_bs = sum(item.subtotal_bs for item in venta_instance.items.all()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                venta_instance.save(update_fields=['total_dolar', 'total_bs'])

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Venta {self.venta.id}"