from django.contrib import admin
from .models import TasaBCV

@admin.register(TasaBCV)
class TasaBCVAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'valor', 'activa')
    list_filter = ('activa', 'fecha')
    search_fields = ('fecha',)