# ventas/admin.py
from django.contrib import admin
from .models import Cliente, Venta, VentaItem # ¡VentaItem en lugar de DetalleVenta!

# Para permitir añadir VentaItems directamente desde la página de Venta
class VentaItemInline(admin.TabularInline):
    model = VentaItem
    extra = 1 # Cuántos formularios vacíos mostrar por defecto
    # Campos que se pueden editar en línea
    fields = ['producto', 'cantidad', 'precio_unitario_dolar', 'precio_unitario_bs']
    readonly_fields = ['precio_unitario_dolar', 'precio_unitario_bs', 'subtotal_dolar', 'subtotal_bs']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'cedula_rif', 'telefono', 'email')
    search_fields = ('nombre', 'apellido', 'cedula_rif', 'telefono')
    list_filter = ('nombre',) # Puedes añadir filtros si tienes muchos clientes

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'cliente', 'usuario', 'total_dolar', 'total_bs', 'metodo_pago', 'estado')
    list_filter = ('fecha', 'metodo_pago', 'estado', 'cliente', 'usuario')
    search_fields = ('cliente__nombre', 'cliente__cedula_rif', 'usuario__username', 'id')
    date_hierarchy = 'fecha' # Para navegar por fecha
    raw_id_fields = ('cliente', 'usuario') # Útil si tienes muchos clientes/usuarios
    inlines = [VentaItemInline] # Agrega el inline para VentaItems

    # Campos que solo se pueden ver en el admin, no editar directamente.
    # Los totales y la tasa se calculan automáticamente
    readonly_fields = ('total_dolar', 'total_bs', 'tasa_bcv_venta') 
    
    # Sobrescribir save_model para asegurar que el usuario loggeado se asigne automáticamente
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Si es una nueva venta
            obj.usuario = request.user # Asigna el usuario loggeado
        super().save_model(request, obj, form, change)