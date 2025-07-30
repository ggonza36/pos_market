# ventas/views_cliente.py
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Cliente
from .forms import ClienteForm
from .views import is_admin_or_propietario # Reutilizamos la función de chequeo de rol
from django.http import JsonResponse

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

class ClienteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Cliente
    template_name = 'ventas/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 15

    def test_func(self):
        return is_venta_staff(self.request.user)

    def get_queryset(self):
        """ Permite buscar clientes por nombre, apellido o cédula. """
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(apellido__icontains=search_query) |
                Q(cedula_rif__icontains=search_query)
            )
        return queryset.order_by('nombre')

class ClienteCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')

    def test_func(self):
        return is_venta_staff(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Nuevo Cliente'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Cliente registrado exitosamente.')
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'ventas/cliente_form.html'
    success_url = reverse_lazy('ventas:cliente_list')

    def test_func(self):
        return is_venta_staff(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cliente'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

class ClienteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Cliente
    template_name = 'ventas/cliente_confirm_delete.html'
    success_url = reverse_lazy('ventas:cliente_list')

    def test_func(self):
        return is_venta_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Cliente '{self.object}' eliminado correctamente.")
        return super().form_valid(form)
    
def get_clientes_ajax(request):
    """
    Busca clientes por término de búsqueda (q) y devuelve una lista JSON.
    """
    search_term = request.GET.get('q', '')
    
    # No buscar si el término es muy corto para mejorar el rendimiento
    if len(search_term) < 2:
        return JsonResponse([], safe=False)

    clientes = Cliente.objects.filter(
        Q(nombre__icontains=search_term) |
        Q(apellido__icontains=search_term) |
        Q(cedula_rif__icontains=search_term)
    ).order_by('nombre')[:10]  # Limita los resultados a 10 para no sobrecargar

    results = []
    for cliente in clientes:
        results.append({
            'id': cliente.id,
            'name': f"{cliente.nombre} {cliente.apellido or ''}".strip(),
            'id_card': cliente.cedula_rif or 'N/A'
        })
    
    return JsonResponse(results, safe=False)