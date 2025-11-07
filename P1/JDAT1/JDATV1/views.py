from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto
from .forms import ProductoForm
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