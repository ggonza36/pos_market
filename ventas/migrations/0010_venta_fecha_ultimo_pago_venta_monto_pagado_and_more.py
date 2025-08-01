# Generated by Django 5.2.3 on 2025-07-10 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0009_alter_venta_metodo_pago'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='fecha_ultimo_pago',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='venta',
            name='monto_pagado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='venta',
            name='estado',
            field=models.CharField(choices=[('ADEUDADO', 'Adeudado'), ('COMPLETADA', 'Completada'), ('ANULADA', 'Anulada'), ('DEVOLUCION', 'Devolución'), ('PARCIALMENTE_PAGADA', 'Parcialmente Pagada')], default='COMPLETADA', max_length=20),
        ),
        migrations.AlterField(
            model_name='venta',
            name='metodo_pago',
            field=models.CharField(choices=[('EFECTIVO', 'Efectivo'), ('TARJETA_DEBITO', 'Tarjeta de Débito'), ('TARJETA_CREDITO', 'Tarjeta de Crédito'), ('TRANSFERENCIA', 'Transferencia'), ('PAGO_MOVIL', 'Pago Móvil'), ('MIXTO', 'Mixto'), ('ZELLE', 'Zelle'), ('CRIPTO', 'Cripto'), ('OTRO', 'Otro'), ('PENDIENTE', 'Pendiente')], default='EFECTIVO', max_length=20),
        ),
    ]
