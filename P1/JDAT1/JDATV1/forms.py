from django import forms
from .models import Producto
from .models import Usuario
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
class usuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'