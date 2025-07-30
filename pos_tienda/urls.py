# urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ventas/', include('ventas.urls')),
    path('inventario/', include('inventario.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('tasas/', include('tasas.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    # Esta ruta ahora será la primera en ser verificada para la URL raíz.
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='index'),
    # Considera si la redirección a 'producto_list' sigue siendo necesaria aquí.
    # Si 'producto_list' es la página de inicio *para usuarios autenticados*,
    # esto se manejaría mejor en tus vistas o con decoradores de login.
    # path('', lambda request: redirect('producto_list')), # Posiblemente eliminar o reubicar.
]