from django import forms
from .models import TasaBCV

class TasaBCVForm(forms.ModelForm):
    class Meta:
        model = TasaBCV
        fields = ['fecha', 'valor', 'activa']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }