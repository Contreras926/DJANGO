from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib import messages

# Create your views here.

def inicio(request):
    return render (request, 'paginas/inicio.html') 

def nosotros (request):
    return render (request, 'paginas/nosotros.html')     

def productos (request):
    productos = Producto.objects.all()
    return render (request, 'productos/index.html', {'productos': productos})

def crear_producto (request):
    formulario = ProductoForm(request.POST or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('productos')
    return render (request, 'productos/crear.html',{'formulario': formulario})

def editar_producto (request, id):
    producto = Producto.objects.get(id=id)
    formulario = ProductoForm(request.POST or None, instance=producto)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('productos')
    return render (request, 'productos/editar.html', {'formulario': formulario})

def eliminar_producto (request, id):
    libro = Producto.objects.get(id=id)
    libro.delete()
    return redirect('productos')

# Registro de usuario
def register(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': UserCreationForm()
        })
    else:
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        username = request.POST.get('username')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'signup.html', {'form': UserCreationForm()})

        try:
            user = User.objects.create_user(username=username, password=password1)
            user.save()
            login(request, user)
            return redirect('inicio')
        except IntegrityError:
            messages.error(request, 'El usuario ya existe')
            return render(request, 'signup.html', {'form': UserCreationForm()})

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
            return render(request, 'signin.html', {'form': AuthenticationForm()})
        else:
            login(request, user)
            return redirect('inicio')
