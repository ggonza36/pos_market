from django.db import migrations

def crear_categorias(apps, schema_editor):
    Categoria = apps.get_model('inventario', 'Categoria')
    categorias = [
        "Alimentos Básicos y Perecederos",
        "Bebidas",
        "Productos Enlatados y Empacados",
        "Limpieza del Hogar",
        "Cuidado Personal",
        "Otros",
        "Charcuteria",
    ]
    for nombre in categorias:
        Categoria.objects.get_or_create(nombre=nombre)

class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_categorias),
    ]