# Generated by Django 5.2.3 on 2025-06-29 19:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('precio_dolar', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_bs', models.DecimalField(decimal_places=2, max_digits=15)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.categoria')),
            ],
        ),
    ]
