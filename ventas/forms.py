# ventas/forms.py
from django import forms
from .models import Venta, VentaItem, Cliente
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from inventario.models import Producto
from crispy_forms.bootstrap import FormActions
from decimal import Decimal, ROUND_HALF_UP

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'cedula_rif', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre del cliente'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Apellido del cliente (opcional)'}),
            'cedula_rif': forms.TextInput(attrs={'placeholder': 'Cédula o RIF (ej: V-12345678)'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Número de teléfono'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Correo electrónico (opcional)'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dirección (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6 mb-0'),
                Column('apellido', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cedula_rif', css_class='form-group col-md-6 mb-0'),
                Column('telefono', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('direccion', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Guardar Cliente', css_class='btn btn-primary mt-3')
        )

class VentaForm(forms.ModelForm):
    # Aquí puedes añadir campos adicionales si los necesitas, como tasa BCV, etc.
    # Pero los campos total_dolar y total_bs no deben estar aquí si son calculados
    # y no editables directamente por el usuario.
    class Meta:
        model = Venta
        fields = [
            'cliente',
            'metodo_pago',
            'estado',
            'observaciones',
            # total_dolar y total_bs no deben estar aquí si son calculados y no editables.
            # Los mostraremos directamente en la plantilla con el JS.
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'cliente': forms.Select(attrs={'class': 'form-control select2-cliente'}), # Añade clase para Select2 si lo usas aquí
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Muy importante si el formulario está dentro de otro form tag (ej: en el template padre)
        self.helper.disable_csrf = True # Deshabilita el token CSRF si ya lo manejas globalmente, si no, déjalo en False o elimínalo

        # Layout para hacer el formulario horizontal
        self.helper.layout = Layout(
            Row(
                Column('cliente', css_class='form-group col-md-6 mb-0'),
                css_class='form-row' # Usa form-row de Bootstrap para el diseño de fila
            ),
            Row(
                Column('metodo_pago', css_class='form-group col-md-6 mb-0'),
                Column('estado', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('observaciones', css_class='form-group col-12 mb-0'), # observaciones a ancho completo
                css_class='form-row'
            ),
            # No incluyas Submit aquí si lo pones fuera del formulario principal en tu template
            # Si lo pones aquí, se renderizará con el formulario principal
            # FormActions(
            #     Submit('submit', 'Guardar Venta', css_class='btn btn-success')
            # )
        )

class VentaItemForm(forms.ModelForm):
    # Campo para mostrar el nombre y detalles del producto en el Select2
    producto_display = forms.CharField(
        label='Producto',
        required=False, # No es estrictamente requerido aquí ya que el 'producto' ID es el que se guarda
        widget=forms.TextInput(attrs={'class': 'form-control select2-producto', 'placeholder': 'Buscar producto por nombre o código'}),
    )

    class Meta:
        model = VentaItem
        fields = [
            'producto',
            'cantidad',
            'precio_unitario_dolar',
            'precio_unitario_bs',
            'subtotal_dolar',
            'subtotal_bs',
        ]
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control select2-producto'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}), # Permite dos decimales, mínimo 0.01
            'precio_unitario_dolar': forms.HiddenInput(),
            'precio_unitario_bs': forms.HiddenInput(),
            'subtotal_dolar': forms.HiddenInput(),
            'subtotal_bs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False # Oculta las etiquetas predeterminadas para un control más fino
        self.helper.form_tag = False
        self.helper.disable_csrf = True # O False si lo quieres habilitado

        # Define el layout para CADA ITEM de venta
        self.helper.layout = Layout(
            Row(
                Column(
                    # El campo producto es el Select2
                    'producto', # Este será el buscador grande
                    HTML('<strong class="producto-nombre-display mt-1"></strong>'), # Aquí se mostrará el nombre después de seleccionar
                    HTML('<small class="text-muted d-block">Stock: <span class="stock-display">0</span> unidades</small>'),
                    css_class='col-md-5 col-sm-12' # Ocupa 5 columnas de 12 para productos
                ),
                Column(
                    HTML('<label for="id_ventaitem_set-__prefix__-cantidad" class="form-label text-muted small mb-0">Cantidad:</label>'),
                    'cantidad',
                    css_class='col-md-2 col-sm-6'
                ),
                Column(
                    HTML('<label class="d-block text-muted small mb-0">P. Unit ($):</label><strong class="precio-unitario-dolar-display"></strong>'),
                    'precio_unitario_dolar', # Campo oculto
                    'precio_unitario_bs', # Campo oculto
                    css_class='col-md-2 col-sm-6'
                ),
                Column(
                    HTML('<label class="d-block text-muted small mb-0">Subtotal ($):</label><strong class="subtotal-dolar-display"></strong>'),
                    'subtotal_dolar', # Campo oculto
                    'subtotal_bs', # Campo oculto
                    css_class='col-md-2 col-sm-6 text-end'
                ),
                Column(
                    HTML('<button type="button" class="btn btn-danger btn-sm delete-row-btn"><i class="bi bi-trash"></i></button>'),
                    'DELETE', # Campo DELETE oculto para formsets
                    css_class='col-md-1 col-sm-6 text-center align-self-center'
                ),
                css_class='venta-item-row'
            )
        )
    
class PagarVentaForm(forms.Form):
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('PAGO_MOVIL', 'Pago Móvil'),
        ('ZELLE', 'Zelle'),
        ('CRIPTO', 'Cripto'),
        ('OTRO', 'Otro'),
    ]

    monto_a_pagar = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Monto a pagar ($)'}),
        help_text='Monto a abonar a la deuda de la venta.'
    )
    metodo_pago_realizado = forms.ChoiceField(
        choices=METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Método de pago utilizado para este abono.'
    )
    observaciones_pago = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Observaciones del pago (opcional)'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.layout = Layout(
            Row(
                Column('monto_a_pagar', css_class='form-group col-md-6 mb-0'),
                Column('metodo_pago_realizado', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('observaciones_pago', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
        )