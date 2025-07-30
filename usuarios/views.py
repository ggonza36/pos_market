from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
# Importaciones para permisos
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Usuario, Rol
from .forms import UsuarioForm

# Importaciones para permisos
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render # Importar render
from django.contrib.auth.decorators import login_required # Importar login_required decorator

def is_admin(user):
    """Checks if the user is authenticated and has 'Admin' role."""
    return user.is_authenticated and hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Admin'

class UsuarioListView(LoginRequiredMixin, UserPassesTestMixin, ListView): # <--- Añade Mixins
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'

    def test_func(self): # <--- Añade este método
        return is_admin(self.request.user)

class UsuarioCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView): # <--- Añade Mixins
    model = Usuario
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_list')

    def test_func(self): # <--- Añade este método
        return is_admin(self.request.user)

class UsuarioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView): # <--- Añade Mixins
    model = Usuario
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_list')

    def test_func(self): # <--- Añade este método
        return is_admin(self.request.user)
    
@login_required # Asegura que el usuario esté logeado para acceder a esta vista
def profile_view(request):
    """
    Vista para mostrar el perfil del usuario logeado.
    Puedes añadir lógica para edición de perfil aquí si es necesario.
    """
    return render(request, 'usuarios/profile.html', {'user': request.user})

@login_required # Asegura que el usuario esté logeado para acceder a esta vista
def settings_view(request):
    """
    Vista para mostrar las configuraciones del usuario.
    Puedes añadir formularios de configuración aquí.
    """
    return render(request, 'usuarios/settings.html', {'user': request.user})