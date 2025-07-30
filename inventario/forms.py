# inventario/forms.py
from django import forms
from .models import Producto, Categoria # Asegúrate de que Categoria esté importada si la usas
from tasas.models import TasaBCV
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages

# Importar las clases de crispy_forms para el layout
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

class ImportarProductosForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (.xlsx)")
    
class ProductoForm(forms.ModelForm):
    porcentaje_ganancia = forms.DecimalField(
        label="Porcentaje de ganancia (%)",
        min_value=0,
        max_value=100,
        initial=35,
        required=True,
        help_text="Ejemplo: 35 para 35%"
    )

    class Meta:
        model = Producto
        fields = [
            'nombre', 'categoria', 'precio_dolar', 'precio_bs', 'stock', 'descripcion',
            'porcentaje_ganancia', 'precio_individual_dolar', 'precio_individual_bs'
        ]
        widgets = {
            'precio_dolar': forms.NumberInput(attrs={'step': '0.01'}),
            'precio_bs': forms.NumberInput(attrs={'step': '0.01',}),
            'stock': forms.NumberInput(attrs={'step': '1', 'min': '0'}),
            'precio_individual_dolar': forms.HiddenInput(),
            'precio_individual_bs': forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Inicializar FormHelper y definir el layout responsive
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6 mb-0'), # Ocupa la mitad del ancho en md y más grandes
                Column('categoria', css_class='form-group col-md-6 mb-0'), # Ocupa la mitad del ancho en md y más grandes
                css_class='form-row' # Clase para filas de Bootstrap 4/5
            ),
            Row(
                Column('precio_dolar', css_class='form-group col-md-6 mb-0'),
                Column('precio_bs', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('porcentaje_ganancia', css_class='form-group col-md-6 mb-0'),
                Column('stock', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            # Los campos que no se incluyan explícitamente en Rows/Columns se renderizarán a ancho completo
            'descripcion', # Este campo se mostrará a ancho completo
            # 'precio_individual_dolar' y 'precio_individual_bs' son HiddenInput y no necesitan ser parte del layout visible
        )
        
        if self.instance.precio_dolar and self.instance.pk:
            if self.instance.precio_bs is not None and self.instance.stock is not None:
                self.initial['precio_dolar'] = (self.instance.precio_dolar * self.instance.stock).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                self.initial['precio_dolar'] = Decimal('0.00')
                
    def clean(self):
        cleaned_data = super().clean()
        request = self.request if hasattr(self, 'request') else None
        
        # Redondear a dos decimales los campos relevantes
        for campo in ['precio_dolar', 'precio_bs', 'porcentaje_ganancia', 'precio_individual_dolar', 'precio_individual_bs']:
            valor = cleaned_data.get(campo)
            if valor is not None:
                cleaned_data[campo] = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Ahora, 'precio_dolar' del formulario es el precio TOTAL para el stock
        precio_dolar_total_input = cleaned_data.get('precio_dolar') 
        stock = cleaned_data.get('stock')
        porcentaje_ganancia = cleaned_data.get('porcentaje_ganancia')
        tasa_bcv_obj = TasaBCV.objects.filter(activa=True).first()

        calculated_unit_precio_dolar = Decimal('0.00')

        # Validar que stock sea positivo si hay un precio total
        if precio_dolar_total_input is not None and precio_dolar_total_input > 0:
            if stock is None or stock <= 0:
                self.add_error('stock', "Si introduces un precio total en Dólares, el stock debe ser mayor que cero.")
                # Establecer valores predeterminados para evitar errores de división por cero o None
                cleaned_data['precio_dolar'] = Decimal('0.00')
                cleaned_data['precio_bs'] = Decimal('0.00')
                cleaned_data['precio_individual_dolar'] = Decimal('0.00')
                cleaned_data['precio_individual_bs'] = Decimal('0.00')
                return cleaned_data # Retorna los datos limpios para mostrar el error

            # Calcular el precio UNITARIO en dólares
            calculated_unit_precio_dolar = (precio_dolar_total_input / Decimal(stock)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Actualizar el campo 'precio_dolar' que se guardará en el modelo (ahora es unitario)
        cleaned_data['precio_dolar'] = calculated_unit_precio_dolar 

        if calculated_unit_precio_dolar is not None and tasa_bcv_obj:
            tasa_bcv = tasa_bcv_obj.valor
            
            # Recalcular precio_bs (precio UNITARIO en Bolívares)
            cleaned_data['precio_bs'] = (calculated_unit_precio_dolar * tasa_bcv).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if porcentaje_ganancia is not None:
                # Calcular precios de venta individuales (precio por unidad con ganancia)
                precio_dolar_con_ganancia = calculated_unit_precio_dolar * (1 + porcentaje_ganancia / Decimal('100'))
                cleaned_data['precio_individual_dolar'] = precio_dolar_con_ganancia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                precio_bs_con_ganancia = cleaned_data['precio_bs'] * (1 + porcentaje_ganancia / Decimal('100'))
                cleaned_data['precio_individual_bs'] = precio_bs_con_ganancia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # Si no hay porcentaje de ganancia, el precio individual es el precio base unitario
                cleaned_data['precio_individual_dolar'] = calculated_unit_precio_dolar.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cleaned_data['precio_individual_bs'] = cleaned_data['precio_bs'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif calculated_unit_precio_dolar is not None and not tasa_bcv_obj:
             if request:
                 messages.warning(request, "No hay una tasa BCV activa. Los precios en Bolívares no se calcularán.")
             cleaned_data['precio_bs'] = Decimal('0.00')
             cleaned_data['precio_individual_dolar'] = calculated_unit_precio_dolar.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
             cleaned_data['precio_individual_bs'] = Decimal('0.00')
        
        return cleaned_data

class ProductoSearchForm(forms.Form):
    q = forms.CharField(
        label="Buscar por nombre, codigo o descripcion",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Buscar productos...', 'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoría",
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    precio_dolar_min = forms.DecimalField(
        label="Precio mínimo (USD)",
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        min_value=0,
        initial=0
    )
    precio_dolar_max = forms.DecimalField(
        label="Precio máximo (USD)",
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        min_value=0,
        initial=Decimal('999999.99')
    )
    precio_bs_min = forms.DecimalField(
        label="Precio mínimo (Bs)",
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        min_value=0,
        initial=0
    )
    precio_bs_max = forms.DecimalField(
        label="Precio máximo (Bs)",
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        min_value=0,
        initial=Decimal('999999.99')
    )