from django.urls import path
from .views import TasaBCVListView, TasaBCVCreateView, TasaBCVUpdateView

urlpatterns = [
    path('lista/', TasaBCVListView.as_view(), name='tasa_list'),
    path('nueva/', TasaBCVCreateView.as_view(), name='tasa_create'),
    path('editar/<int:pk>/', TasaBCVUpdateView.as_view(), name='tasa_update'),
]