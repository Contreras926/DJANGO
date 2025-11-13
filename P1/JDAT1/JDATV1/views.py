from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.db import IntegrityError
# Create your views here.

def inicio(request):
    return render (request, 'paginas/inicio.html')   

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

def signup(request):
    
    if request.method == 'GET':
        return render (request, 'paginas/signup.html' , {
        'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:    
            try:
                #Registrar usuario
                user = User.objects.create_user(username=request.POST['usename'], password=request.
                post['password1'])
                user.save()
                login(request, user)
                return redirect('inicio')
            except IntegrityError:
                return render (request, 'paginas/signup.html' , {
                'form': UserCreationForm,
                "error": 'Usuario ya existe'
                })
        return render (request, 'paginas/signup.html' , {
            'form': UserCreationForm,
            "error": HttpResponse('Contraseñas no coinciden')
        })
            
def signout(request):
    logout(request)
    return redirect('inicio')                
        
    