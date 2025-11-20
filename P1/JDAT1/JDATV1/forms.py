from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario
from .models import Producto

class RegistroForm(forms.ModelForm): 
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput
    )
    class Meta:
        model = Usuario
        fields = ['nombreUsuario', 'apellidoUsuario', 'correo', 'rol']

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Correo Electrónico')

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
