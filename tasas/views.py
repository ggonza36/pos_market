from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import TasaBCV
from .forms import TasaBCVForm

class TasaBCVListView(ListView):
    model = TasaBCV
    template_name = 'tasas/tasa_list.html'
    context_object_name = 'tasas'

class TasaBCVCreateView(CreateView):
    model = TasaBCV
    form_class = TasaBCVForm
    template_name = 'tasas/tasa_form.html'
    success_url = reverse_lazy('tasa_list')

class TasaBCVUpdateView(UpdateView):
    model = TasaBCV
    form_class = TasaBCVForm
    template_name = 'tasas/tasa_form.html'
    success_url = reverse_lazy('tasa_list')