from django.urls import path
from .views import ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView, importar_productos, descargar_plantilla_productos, descargar_productos_bajo_stock_pdf

urlpatterns = [
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/editar/<int:pk>/', ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', ProductoDeleteView.as_view(), name='producto_delete'),
    path('productos/importar/', importar_productos, name='importar_productos'),
    path('productos/plantilla/', descargar_plantilla_productos, name='descargar_plantilla_productos'),
    path('productos/stock_bajo/pdf/', descargar_productos_bajo_stock_pdf, name='descargar_productos_bajo_stock_pdf'),
]