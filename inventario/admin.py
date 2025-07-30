from django.contrib import admin
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'codigo', 'categoria', 'precio_dolar', 'precio_bs', 'stock')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'codigo')