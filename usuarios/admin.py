from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )