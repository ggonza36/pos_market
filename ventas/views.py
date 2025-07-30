# ventas/views.py
import json
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View # Añadido TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, F # Importado Sum
from django.utils import timezone # Importado timezone

from usuarios.models import Rol
from .models import Venta, VentaItem, Cliente
from .forms import VentaForm, VentaItemForm, PagarVentaForm
from inventario.models import Producto
from tasas.models import TasaBCV
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings # Importar settings
import os # Importar os para manipulación de rutas
import base64 # Importar base64 para codificación

from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

def is_admin(user):
    """Checks if the user is authenticated and has 'Admin' role."""
    return user.is_authenticated and hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Admin'

def is_propietario(user):
    """Checks if the user is authenticated and has 'Propietario' role."""
    return user.is_authenticated and hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Propietario'

def is_vendedor(user):
    """Checks if the user is authenticated and has 'Vendedor' role."""
    return user.is_authenticated and hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Vendedor'

def is_admin_or_propietario(user):
    """Checks if the user is authenticated and has 'Admin' or 'Propietario' role."""
    return is_admin(user) or is_propietario(user)

def is_venta_staff(user):
    """Checks if the user is authenticated and has 'Admin', 'Propietario', or 'Vendedor' role."""
    return is_admin(user) or is_propietario(user) or is_vendedor(user)

# Se establece extra=1 para que siempre muestre al menos un formulario de item,
# los demás se agregarán dinámicamente con JS.
VentaItemFormSet = inlineformset_factory(
    Venta,
    VentaItem,
    form=VentaItemForm,
    extra=1,
    can_delete=True
)

class VentaListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Venta
    template_name = 'ventas/ventas_dashboard.html'
    context_object_name = 'ventas'
    ordering = ['-fecha'] # Ordenar por fecha descendente
    paginate_by = 5 # Paginación de 10 ventas por página
    
    def test_func(self):
        return is_venta_staff(self.request.user)
    
    def get_queryset(self):
        """
        Filtra el queryset de ventas basado en los parámetros GET 'period' y 'status'.
        """
        queryset = super().get_queryset()
        period = self.request.GET.get('period', 'all')
        status_filter = self.request.GET.get('status', '')

        # Filtrar por estado si se especifica
        if status_filter == 'ADEUDADO':
            queryset = queryset.filter(estado='ADEUDADO')
            
        # Filtrar por período de tiempo
        today = timezone.localdate()
        if period == 'today':
            queryset = queryset.filter(fecha__date=today)
        elif period == 'month':
            month_start = today.replace(day=1)
            queryset = queryset.filter(fecha__date__gte=month_start, fecha__date__lte=today)
        elif period == 'year':
            year_start = today.replace(month=1, day=1)
            queryset = queryset.filter(fecha__date__gte=year_start, fecha__date__lte=today)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_status = self.request.GET.get('status', 'all')
        
        if current_status == 'all':
            context['current_status_display'] = 'Todos'
        elif current_status == 'adeudado':
            context['current_status_display'] = 'Adeudado'
        elif current_status == 'completada':
            context['current_status_display'] = 'Completada'
        elif current_status == 'parcialmente_pagada':
            context['current_status_display'] = 'Parcialmente Pagada'
        elif current_status == 'anulada':
            context['current_status_display'] = 'Anulada'
        else:
            context['current_status_display'] = current_status.replace('_', ' ').capitalize()
        
        # Los KPIs se calculan sobre el total de ventas, sin importar el filtro de la tabla
        today = timezone.localdate()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        all_ventas = Venta.objects.all()
        total_ventas_hoy = all_ventas.filter(fecha__date=today).aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')
        total_ventas_mes = all_ventas.filter(fecha__date__gte=month_start, fecha__date__lte=today).aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')
        total_ventas_annio = all_ventas.filter(fecha__date__gte=year_start).aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')
        total_ventas_adeudadas = Venta.objects.filter(estado='ADEUDADO').aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')
        
        try:
            tasa_bcv_activa = TasaBCV.objects.latest('fecha').valor
        except TasaBCV.DoesNotExist:
            tasa_bcv_activa = Decimal('1.00')
            
        total_ventas_hoy_bs = (total_ventas_hoy * tasa_bcv_activa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Pasar los datos de KPIs y estado de los filtros al contexto
        context['total_ventas_hoy'] = total_ventas_hoy
        context['total_ventas_hoy_bs'] = total_ventas_hoy_bs
        context['total_ventas_mes'] = total_ventas_mes
        context['total_ventas_annio'] = total_ventas_annio
        context['total_ventas_adeudadas'] = total_ventas_adeudadas
        context['tasa_bcv_activa'] = tasa_bcv_activa
        context['payment_form'] = PagarVentaForm()
        
        # Pasar los filtros actuales para que el template pueda resaltar el botón activo
        context['current_period'] = self.request.GET.get('period', 'all')
        context['current_status'] = self.request.GET.get('status', '')
        
        return context

class VentaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Venta
    form_class = VentaForm
    template_name = 'ventas/venta_form.html'
    success_url = reverse_lazy('ventas:venta_dashboard')
    
    def test_func(self): # <--- Añade este método
        return is_venta_staff(self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = VentaItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = VentaItemFormSet(instance=self.object)
        
        try:
            data['tasa_bcv_activa'] = TasaBCV.objects.latest('fecha').valor # Usando .valor para la tasa activa
        except TasaBCV.DoesNotExist:
            data['tasa_bcv_activa'] = Decimal('1.00') # Valor por defecto
            messages.warning(self.request, "No se ha registrado una tasa BCV activa. Se usará 1.00 por defecto.")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        # El nombre del formset es 'items' en CreateView y 'formset' en UpdateView
        # Asegurémonos de usar el correcto en cada caso.
        # En tu código, usas 'items' en CreateView y 'formset' en UpdateView
        # pero la lógica dentro de los `form_valid` usa `items` y `formset` de manera inconsistente
        # Lo estandarizaremos a `formset`.
        formset = context.get('items') or context.get('formset')
        
        # ELIMINADO: La asignación de form.instance.tasa_bcv_venta que ya no existe

        with transaction.atomic():
            self.object = form.save(commit=False)
            if not self.object.usuario_id:
                self.object.usuario = self.request.user
            self.object.save()
            
            if formset.is_valid():
                formset.instance = self.object
                
                # --- LÓGICA SIMPLIFICADA ---
                # Ya no calculamos los subtotales aquí. Solo validamos stock y guardamos.
                # El modelo `VentaItem.save()` se encargará de todos los cálculos.
                
                # Guardamos los items del formset
                items_to_save = []
                for item_form in formset:
                    if item_form.is_valid() and item_form.cleaned_data.get('producto'):
                        # Se gestiona la devolución de stock para items borrados
                        if item_form.cleaned_data.get('DELETE'):
                            if item_form.instance.pk:
                                item_form.instance.producto.stock += item_form.instance.cantidad
                                item_form.instance.producto.save(update_fields=['stock'])
                                item_form.instance.delete()
                            continue

                        item = item_form.save(commit=False)
                        
                        # Lógica de validación de stock (esto es importante y debe quedar aquí)
                        original_cantidad = 0
                        if item.pk:
                            original_cantidad = VentaItem.objects.get(pk=item.pk).cantidad
                        
                        cantidad_diff = item.cantidad - original_cantidad
                        
                        if cantidad_diff > item.producto.stock:
                             messages.error(self.request, f"Stock insuficiente para {item.producto.nombre}. Disponible: {item.producto.stock}. Requerido adicionalmente: {cantidad_diff}")
                             raise ValueError("Stock insuficiente.")
                        
                        # No actualizamos el stock aquí, el modelo lo hará
                        items_to_save.append(item)
                
                # Guardamos todos los items. Esto disparará los métodos .save() del modelo
                # y los totales de la venta se actualizarán automáticamente.
                for item in items_to_save:
                    item.save()
                
                # Opcional: refrescar el objeto Venta para asegurar que tiene los totales actualizados
                self.object.refresh_from_db()

                messages.success(self.request, "Venta guardada exitosamente.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, f"Por favor, corrige los errores en los productos de la venta: {formset.errors}")
                return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['formset'] = VentaItemFormSet(self.request.POST, instance=self.object)
        messages.error(self.request, "Hubo errores al guardar la venta. Por favor, revisa los campos.")
        return self.render_to_response(context)

class VentaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Venta
    form_class = VentaForm
    template_name = 'ventas/venta_form.html'
    success_url = reverse_lazy('ventas:venta_dashboard') # Corregido a 'ventas:venta_list'
    
    def test_func(self): # <--- Añade este método
        return is_admin_or_propietario(self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = VentaItemFormSet(self.request.POST, instance=self.object)
        else:
            data['formset'] = VentaItemFormSet(instance=self.object)
        
        try:
            data['tasa_bcv_activa'] = TasaBCV.objects.latest('fecha').valor # Usando .valor para la tasa activa
        except TasaBCV.DoesNotExist:
            data['tasa_bcv_activa'] = Decimal('1.00')
            messages.warning(self.request, "No se ha registrado una tasa BCV activa. Se usará 1.00 por defecto.")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        # El nombre del formset es 'items' en CreateView y 'formset' en UpdateView
        # Asegurémonos de usar el correcto en cada caso.
        # En tu código, usas 'items' en CreateView y 'formset' en UpdateView
        # pero la lógica dentro de los `form_valid` usa `items` y `formset` de manera inconsistente
        # Lo estandarizaremos a `formset`.
        formset = context.get('items') or context.get('formset')
        
        # ELIMINADO: La asignación de form.instance.tasa_bcv_venta que ya no existe

        with transaction.atomic():
            self.object = form.save(commit=False)
            if not self.object.usuario_id:
                self.object.usuario = self.request.user
            self.object.save()
            
            if formset.is_valid():
                formset.instance = self.object
                
                # --- LÓGICA SIMPLIFICADA ---
                # Ya no calculamos los subtotales aquí. Solo validamos stock y guardamos.
                # El modelo `VentaItem.save()` se encargará de todos los cálculos.
                
                # Guardamos los items del formset
                items_to_save = []
                for item_form in formset:
                    if item_form.is_valid() and item_form.cleaned_data.get('producto'):
                        # Se gestiona la devolución de stock para items borrados
                        if item_form.cleaned_data.get('DELETE'):
                            if item_form.instance.pk:
                                item_form.instance.producto.stock += item_form.instance.cantidad
                                item_form.instance.producto.save(update_fields=['stock'])
                                item_form.instance.delete()
                            continue

                        item = item_form.save(commit=False)
                        
                        # Lógica de validación de stock (esto es importante y debe quedar aquí)
                        original_cantidad = 0
                        if item.pk:
                            original_cantidad = VentaItem.objects.get(pk=item.pk).cantidad
                        
                        cantidad_diff = item.cantidad - original_cantidad
                        
                        if cantidad_diff > item.producto.stock:
                             messages.error(self.request, f"Stock insuficiente para {item.producto.nombre}. Disponible: {item.producto.stock}. Requerido adicionalmente: {cantidad_diff}")
                             raise ValueError("Stock insuficiente.")
                        
                        # No actualizamos el stock aquí, el modelo lo hará
                        items_to_save.append(item)
                
                # Guardamos todos los items. Esto disparará los métodos .save() del modelo
                # y los totales de la venta se actualizarán automáticamente.
                for item in items_to_save:
                    item.save()
                
                # Opcional: refrescar el objeto Venta para asegurar que tiene los totales actualizados
                self.object.refresh_from_db()

                messages.success(self.request, "Venta guardada exitosamente.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, f"Por favor, corrige los errores en los productos de la venta: {formset.errors}")
                return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['formset'] = VentaItemFormSet(self.request.POST, instance=self.object)
        messages.error(self.request, "Hubo errores al actualizar la venta. Por favor, revisa los campos.")
        return self.render_to_response(context)


class VentaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Venta
    template_name = 'ventas/venta_confirm_delete.html' # Necesitarás crear este template
    success_url = reverse_lazy('ventas:venta_dashboard')
    
    def test_func(self): # <--- Añade este método
        return is_venta_staff(self.request.user)

    def form_valid(self, form):
        # Antes de eliminar la venta, devuelve el stock de todos los ítems asociados
        with transaction.atomic():
            for item in self.object.items.all():
                producto = item.producto
                producto.stock += item.cantidad # Devuelve la cantidad al stock
                producto.save(update_fields=['stock'])
            messages.success(self.request, "Venta eliminada y stock de productos devuelto correctamente.")
        return super().form_valid(form)


#@method_decorator
def get_product_details_ajax(request):
    search_term = request.GET.get('search', '')
    product_id = request.GET.get('id') # Nuevo parámetro para buscar por ID
    page = int(request.GET.get('page', 1))
    results_per_page = 10 # Define cuántos resultados quieres por página

    products = Producto.objects.all()

    if product_id:
        # Si se proporciona un ID, buscar el producto exacto
        products = products.filter(id=product_id)
    elif search_term:
        # Si hay un término de búsqueda, filtrar por nombre o código
        products = products.filter(
            Q(nombre__icontains=search_term) | Q(codigo__icontains=search_term)
        )
    
    products = products.order_by('nombre') # Ordenar siempre

    total_count = products.count()
    
    start = (page - 1) * results_per_page
    end = start + results_per_page
    paginated_products = products[start:end]

    product_list = []
    for product in paginated_products:
        product_list.append({
            'id': product.id,
            # Asegúrate de usar precio_individual_dolar y precio_individual_bs aquí
            'text': f"{product.nombre} (Cod: {product.codigo}, Stock: {product.stock}, ${product.precio_individual_dolar.quantize(Decimal('0.01'))})", # Para Select2, mostrando precio individual
            'nombre': product.nombre,
            'codigo': product.codigo,
            'precio_individual_dolar': str(product.precio_individual_dolar), # <-- CAMBIO CLAVE
            'precio_individual_bs': str(product.precio_individual_bs),       # <-- CAMBIO CLAVE
            'stock': product.stock,
            'unidad_medida': product.unidad_medida if hasattr(product, 'unidad_medida') else '', # Si tienes este campo
        })

    return JsonResponse({
        'results': product_list,
        'pagination': {
            'more': end < total_count
        }
    })
    
class PagarVentaView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Solo administradores, propietarios o vendedores pueden registrar pagos
        return is_venta_staff(self.request.user)

    @method_decorator(require_POST) # Asegura que solo acepta POST requests
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        venta = get_object_or_404(Venta, pk=pk)
        form = PagarVentaForm(request.POST)

        if form.is_valid():
            monto_a_pagar = form.cleaned_data['monto_a_pagar']
            metodo_pago_realizado = form.cleaned_data['metodo_pago_realizado']
            observaciones_pago = form.cleaned_data.get('observaciones_pago', '')

            # Paso 1: Validar si el monto a pagar es válido en Python
            if monto_a_pagar <= Decimal('0'):
                return JsonResponse({
                    'success': False,
                    'message': 'El monto a pagar debe ser mayor a cero.',
                    'errors': {'monto_a_pagar': [{'message': 'Debe ser mayor a cero.'}]}
                }, status=400)

            # Validar que el monto a pagar no exceda el restante actual
            # Aquí, venta.monto_restante ya es un objeto Decimal
            if monto_a_pagar > venta.monto_restante: 
                return JsonResponse({
                    'success': False,
                    'message': f'El monto a pagar (${monto_a_pagar}) excede el monto restante (${venta.monto_restante}).',
                    'errors': {'monto_a_pagar': [{'message': 'El monto excede lo adeudado.'}]}
                }, status=400)

            try:
                with transaction.atomic():
                    # Solo actualizamos 'monto_pagado' en la base de datos
                    # 'monto_restante' se recalculará automáticamente al ser una propiedad
                    Venta.objects.filter(pk=venta.pk).update(
                        monto_pagado=F('monto_pagado') + monto_a_pagar
                    )
                    
                    # Recargar la instancia para obtener los valores actualizados
                    # Esto es crucial para que 'venta.monto_restante' tenga el valor correcto
                    venta.refresh_from_db()

                    # Determinar el nuevo estado basado en el monto_restante actualizado
                    if venta.monto_restante.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) <= Decimal('0.00'):
                        venta.estado = 'COMPLETADA'
                    elif venta.monto_restante.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) > Decimal('0.00') and venta.monto_pagado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) > Decimal('0.00'):
                        venta.estado = 'PARCIALMENTE_PAGADA'
                    else:
                        # Si no se cumple ninguna de las anteriores (ej. venta.monto_pagado es 0),
                        # y venta.monto_restante es > 0, podría permanecer como ADEUDADO o el estado inicial.
                        # Asume que si no es completada o parcialmente pagada, se mantiene el estado anterior
                        # o un estado por defecto como 'ADEUDADO' si no se pagó nada.
                        # Si antes era ADEUDADO y sigue quedando, no cambia a PARCIALMENTE_PAGADA,
                        # pero ya la segunda condición lo cubre.
                        # Este 'else' podría ser redundante si los estados son bien manejados.
                        # Opcionalmente: venta.estado = 'ADEUDADO' si el monto pagado es 0 y aún hay restante.
                        pass # No cambiar el estado si ya está cubierto o no aplica

                    # Guardar el estado (y solo el estado si ya actualizamos monto_pagado arriba)
                    # Si haces .update() con F, y luego haces .save(), asegúrate de qué campos actualizas
                    # O podrías hacer todo el cambio de estado en el update() inicial.
                    # Para simplificar y dado que ya recargaste la instancia, solo guarda el estado.
                    venta.save(update_fields=['estado']) # Solo guardamos el estado ahora que está definido


                    # Opcional: Crear un registro de pago si tienes un modelo para ello
                    # from .models import PagoVenta
                    # PagoVenta.objects.create(
                    #     venta=venta,
                    #     monto=monto_a_pagar,
                    #     metodo_pago=metodo_pago_realizado,
                    #     observaciones=observaciones_pago,
                    #     registrado_por=request.user
                    # )

                    return JsonResponse({'success': True, 'message': 'Pago registrado exitosamente.'})

            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error al procesar el pago: {str(e)}'}, status=500)
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [{'message': error} for error in field_errors]
            
            return JsonResponse({
                'success': False,
                'message': 'Datos del formulario inválidos.',
                'errors': errors
            }, status=400)

# *** NUEVO: Vista para generar PDF de Ventas Adeudadas ***
class VentasAdeudadasPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_venta_staff(self.request.user)

    def get(self, request, *args, **kwargs):
        ventas_adeudadas = Venta.objects.filter(estado='ADEUDADO').order_by('-fecha')
        total_adeudado = ventas_adeudadas.aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')

        context = {
            'ventas': ventas_adeudadas,
            'total_adeudado': total_adeudado,
            'current_date': timezone.localdate(),
        }
        
        # Renderizar la plantilla HTML a PDF
        template_path = 'ventas/ventas_adeudadas_pdf.html' # Necesitarás crear esta plantilla
        template = get_template(template_path)
        html = template.render(context)

        # Crear un objeto BytesIO para guardar el archivo PDF
        result = BytesIO()

        # Generar el PDF
        pisa_status = pisa.CreatePDF(
            html,                # the HTML to convert
            dest=result,         # file handle to receive result
            link_callback=lambda uri, rel: os.path.join(settings.BASE_DIR, uri.replace(settings.STATIC_URL, 'static/')) # Esto es un ejemplo, ajusta según tu configuración de STATIC_ROOT
        )

        # Si hay errores en la generación
        if pisa_status.err:
            return HttpResponse('Error al generar el PDF: %s' % html, status=500)
        
        # Devolver el PDF como respuesta
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="ventas_adeudadas.pdf"'
        return response
# *** FIN NUEVO ***

@csrf_exempt
@require_POST
def registrar_venta_pos_ajax(request):
    try:
        data = json.loads(request.body)
        items_data = data.get('items', {})
        cliente_id = data.get('cliente_id')

        if not items_data:
            return JsonResponse({'status': 'error', 'message': 'No hay productos en la venta.'}, status=400)

        with transaction.atomic():
            try:
                tasa_activa = TasaBCV.objects.latest('fecha').valor
            except TasaBCV.DoesNotExist:
                tasa_activa = Decimal('1.00')

            cliente_instance = None
            if cliente_id is not None:
                try:
                    cliente_id = int(cliente_id)
                    cliente_instance = Cliente.objects.get(pk=cliente_id)
                except (ValueError, Cliente.DoesNotExist):
                    raise ValueError(f"El cliente con ID '{data.get('cliente_id')}' no es válido o no existe.")

            nueva_venta = Venta.objects.create(
                usuario=request.user,
                cliente=cliente_instance,
                metodo_pago=data.get('metodo_pago'),
                estado=data.get('estado_venta'),
                tasa_bcv_venta=tasa_activa,
            )

            for product_id, item_data in items_data.items():
                producto = Producto.objects.get(pk=product_id)
                cantidad = Decimal(str(item_data.get('quantity', 0)))

                if cantidad <= 0:
                    continue

                if cantidad > producto.stock:
                    raise ValueError(f"Stock insuficiente para el producto: {producto.nombre}")

                VentaItem.objects.create(
                    venta=nueva_venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_dolar=producto.precio_individual_dolar,
                    precio_unitario_bs=(producto.precio_individual_dolar * tasa_activa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                )

            nueva_venta.refresh_from_db()

            # --- INICIO: Lógica de generación de PDF ---
            context = {
                'venta': nueva_venta,
                'settings': settings, # Pasa la configuración si la necesitas en la plantilla para STATIC_URL, etc.
            }
            
            template_path = 'ventas/mini_factura_pdf.html'
            template = get_template(template_path)
            html = template.render(context)

            result = BytesIO()

            pisa_status = pisa.CreatePDF(
                html,
                dest=result,
                # link_callback=lambda uri, rel: os.path.join(settings.BASE_DIR, uri.replace(settings.STATIC_URL, 'static/')) # Ejemplo, ajustar según sea necesario
            )

            if pisa_status.err:
                return JsonResponse({'status': 'error', 'message': f'Error al generar el PDF: {pisa_status.err}'}, status=500)
            
            # Codificar el contenido del PDF a base64
            pdf_base64 = base64.b64encode(result.getvalue()).decode('utf-8')
            # --- FIN: Lógica de generación de PDF ---

            return JsonResponse({
                'status': 'success',
                'message': 'Venta registrada exitosamente.',
                'venta_id': nueva_venta.id,
                'pdf_receipt': pdf_base64, # Envía el PDF codificado en base64
                'pdf_filename': f'factura_venta_{nueva_venta.id}.pdf' # Sugiere un nombre de archivo para el cliente
            })

    except Producto.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Uno de los productos no fue encontrado.'}, status=404)
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc() # Para depuración, imprime el rastreo completo en la consola
        return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)
    
class DeudasPorClientePDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_venta_staff(self.request.user)

    def get(self, request, *args, **kwargs):
        # Agrupar las deudas por cliente y sumar el total en dólares
        deudas_por_cliente = Venta.objects.filter(
            estado='ADEUDADO',
            cliente__isnull=False  # Solo ventas asociadas a un cliente
        ).values(
            'cliente__id', # Agrupar por ID de cliente
            'cliente__nombre', 
            'cliente__apellido', 
            'cliente__cedula_rif'
        ).annotate(
            total_adeudado=Sum('total_dolar') # Sumar el total en dólares para cada grupo
        ).order_by('-total_adeudado') # Ordenar de mayor a menor deuda

        # Calcular el total general de todas las deudas
        total_general_adeudado = Venta.objects.filter(estado='ADEUDADO').aggregate(Sum('total_dolar'))['total_dolar__sum'] or Decimal('0.00')

        context = {
            'deudas_por_cliente': deudas_por_cliente,
            'total_general_adeudado': total_general_adeudado,
            'current_date': timezone.localdate(),
        }
        
        # Renderizar la nueva plantilla HTML a PDF
        template_path = 'ventas/deudas_por_cliente_pdf.html' # Nueva plantilla
        template = get_template(template_path)
        html = template.render(context)

        result = BytesIO()

        pisa_status = pisa.CreatePDF(
            html,
            dest=result,
            link_callback=lambda uri, rel: os.path.join(settings.BASE_DIR, uri.replace(settings.STATIC_URL, 'static/'))
        )

        if pisa_status.err:
            return HttpResponse('Error al generar el PDF: %s' % html, status=500)
        
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="resumen_deudas_por_cliente.pdf"'
        return response