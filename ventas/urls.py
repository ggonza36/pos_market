# ventas/urls.py
from django.urls import path, include
from django.views.generic import RedirectView
from . import views
from .views import (
    VentaListView,
    VentaCreateView,
    VentaUpdateView,
    VentaDeleteView,
    get_product_details_ajax,
    registrar_venta_pos_ajax,
    VentaListView as VentasDashboardView,
    VentasAdeudadasPDFView,
    DeudasPorClientePDFView,
)
# ANOTACIÓN: Importar las nuevas vistas de cliente
from .views_cliente import (
    ClienteListView,
    ClienteCreateView,
    ClienteUpdateView,
    ClienteDeleteView,
    get_clientes_ajax,
)

app_name = 'ventas'

# ANOTACIÓN: Se agrupan las URLs por funcionalidad para mayor claridad
venta_patterns = [
    # La URL 'lista/' ahora apunta al dashboard, que ya contiene la lista.
    path('', VentaListView.as_view(), name='venta_list'),
    path('nueva/', VentaCreateView.as_view(), name='venta_create'),
    path('editar/<int:pk>/', VentaUpdateView.as_view(), name='venta_update'),
    path('eliminar/<int:pk>/', VentaDeleteView.as_view(), name='venta_delete'),
    path('pagar/<int:pk>/', views.PagarVentaView.as_view(), name='venta_pagar'),
]

cliente_patterns = [
    path('', ClienteListView.as_view(), name='cliente_list'),
    path('nuevo/', ClienteCreateView.as_view(), name='cliente_create'),
    path('editar/<int:pk>/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('eliminar/<int:pk>/', ClienteDeleteView.as_view(), name='cliente_delete'),
]

api_patterns = [
    path('get_product_details/', get_product_details_ajax, name='get_product_details_ajax'),
    path('get_clientes/', get_clientes_ajax, name='get_clientes_ajax'), # ANOTACIÓN: Nueva URL para buscar clientes
    path('registrar-venta/', registrar_venta_pos_ajax, name='registrar_venta_pos_ajax'),
]

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=False), name='index'),
    path('dashboard/', VentasDashboardView.as_view(), name='ventas_dashboard'),
    
    # ANOTACIÓN: Se incluyen los patrones de URL agrupados
    path('transacciones/', include(venta_patterns)),
    path('clientes/', include(cliente_patterns)),
    path('api/', include(api_patterns)),
    path('ventas_adeudadas/pdf/', VentasAdeudadasPDFView.as_view(), name='ventas_adeudadas_pdf'),
    path('reportes/deudas_por_cliente/pdf/', DeudasPorClientePDFView.as_view(), name='deudas_por_cliente_pdf'),
]