# inventario/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producto
from tasas.models import TasaBCV
from decimal import Decimal, ROUND_HALF_UP

@receiver(post_save, sender=TasaBCV)
def recalculate_product_prices_on_tasa_change(sender, instance, **kwargs):
    """
    Recalcula los precios en Bolívares y los precios individuales
    de todos los productos cuando una TasaBCV se activa.
    """
    # Solo ejecutar si la instancia de TasaBCV que se acaba de guardar está activa
    if instance.activa:
        active_tasa_bcv = instance.valor
        
        products_to_update = []
        for product in Producto.objects.all().iterator():
            original_precio_bs = product.precio_bs
            original_precio_individual_dolar = product.precio_individual_dolar
            original_precio_individual_bs = product.precio_individual_bs

            # --- Lógica para precio_individual_dolar (NO DEBE CAMBIAR CON TASA BCV) ---
            # Calcular precio_individual_dolar basado solo en precio_dolar y porcentaje_ganancia
            # Este cálculo NO debe depender de active_tasa_bcv
            if product.porcentaje_ganancia is not None:
                # Si hay porcentaje de ganancia, aplicarlo al precio_dolar para obtener el precio de venta en Dólares
                precio_dolar_con_ganancia = product.precio_dolar * (1 + product.porcentaje_ganancia / Decimal('100'))
                product.precio_individual_dolar = precio_dolar_con_ganancia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # Si no hay porcentaje de ganancia, el precio individual en Dólares es el precio base en Dólares
                if product.precio_dolar is not None:
                    product.precio_individual_dolar = product.precio_dolar.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    product.precio_individual_dolar = None # O manejar como prefieras si precio_dolar es None
            # --- FIN de Lógica para precio_individual_dolar ---

            # Recalcular precio_bs (precio base en Bs) - Este SÍ se ve afectado por TasaBCV
            if product.precio_dolar is not None and active_tasa_bcv is not None:
                product.precio_bs = (product.precio_dolar * active_tasa_bcv).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                product.precio_bs = None # O manejar como prefieras si precio_dolar o active_tasa_bcv es None
            
            # Recalcular precio_individual_bs (precio de venta en Bs) - Este SÍ se ve afectado por TasaBCV
            # Asegurarse de usar el precio_bs recién calculado y el porcentaje de ganancia
            if product.precio_bs is not None and product.porcentaje_ganancia is not None:
                precio_bs_con_ganancia = product.precio_bs * (1 + product.porcentaje_ganancia / Decimal('100'))
                product.precio_individual_bs = precio_bs_con_ganancia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            elif product.precio_bs is not None: # Si no hay porcentaje de ganancia, pero sí precio_bs
                product.precio_individual_bs = product.precio_bs.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                product.precio_individual_bs = None # O manejar como prefieras


            # Solo añadir a la lista si algún precio relevante ha cambiado
            if (product.precio_bs != original_precio_bs or 
                product.precio_individual_dolar != original_precio_individual_dolar or # Aunque no debería cambiar si el precio_dolar_base no cambia
                product.precio_individual_bs != original_precio_individual_bs):
                products_to_update.append(product)
        
        # Realizar una actualización masiva para mejorar el rendimiento
        if products_to_update:
            Producto.objects.bulk_update(
                products_to_update, 
                ['precio_bs', 'precio_individual_dolar', 'precio_individual_bs']
            )