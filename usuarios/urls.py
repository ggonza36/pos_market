from django.urls import path
from .views import UsuarioListView, UsuarioCreateView, UsuarioUpdateView, profile_view, settings_view

urlpatterns = [
    path('lista/', UsuarioListView.as_view(), name='usuario_list'),
    path('nuevo/', UsuarioCreateView.as_view(), name='usuario_create'),
    path('editar/<int:pk>/', UsuarioUpdateView.as_view(), name='usuario_update'),
    path('perfil/', profile_view, name='profile'), # Nueva URL para el perfil
    path('configuracion/', settings_view, name='settings'), # Nueva URL para la configuración
]