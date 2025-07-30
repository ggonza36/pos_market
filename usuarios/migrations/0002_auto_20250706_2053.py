from django.db import migrations

def create_roles(apps, schema_editor):
    Rol = apps.get_model('usuarios', 'Rol')
    
    # Lista de roles a crear
    roles = ['Admin', 'Propietario', 'Vendedor']
    
    for role_name in roles:
        Rol.objects.get_or_create(nombre=role_name)

class Migration(migrations.Migration):

    dependencies = [
        # Asegúrate de que esta dependencia apunte a la migración anterior correcta de tu app 'usuarios'.
        # Por ejemplo, si tu migración anterior fue 0001_initial.py, podría ser:
        ('usuarios', '0001_initial'),
        # O la migración que creó el modelo Rol si no es la inicial
    ]

    operations = [
        migrations.RunPython(create_roles),
    ]