from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, FloatField
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Venta



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


#@login_required
@transaction.atomic
def registrar_venta(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Cantidad inválida.')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a cero')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        # Bloquear el producto para evitar condiciones de carrera
        producto = Producto.objects.select_for_update().get(id=id)
        
        if cantidad > producto.stockActual:
            messages.error(request, f'Stock insuficiente. Stock actual: {producto.stockActual}')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        # Registrar la venta - USANDO preciolmitario (tu campo actual)
        Venta.objects.create(
            producto=producto,
            cantidad=cantidad,
            precio_venta=producto.precioUnitario  # ← USA preciolmitario
        )
        
        # Actualizar stock
        producto.stockActual -= cantidad
        producto.save()
        
        messages.success(request, f'Venta registrada: {cantidad} unidades de {producto.nombreProducto}')
        return redirect('productos')
    
    return render(request, 'ventas/registrar.html', {'producto': producto})

#@login_required
def reportes_ventas(request):
    # Obtener filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    ventas = Venta.objects.select_related('producto').all()

    # Aplicar filtros de fecha
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            ventas = ventas.filter(fecha_venta__date__gte=fecha_inicio_dt)
        except ValueError:
            fecha_inicio = None
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            ventas = ventas.filter(fecha_venta__date__lte=fecha_fin_dt)
        except ValueError:
            fecha_fin = None
    
    # Cálculos
    ventas_stats = ventas.aggregate(
        total_ventas=Sum('cantidad'),
        ingresos_totales=Sum(F('cantidad') * F('precio_venta'), output_field=FloatField())
    )
    
    total_ventas = ventas_stats['total_ventas'] or 0
    ingresos_totales = ventas_stats['ingresos_totales'] or 0.0
    
    # DATOS PARA GRÁFICA DE VENTAS POR PRODUCTO
    ventas_por_producto_qs = ventas.values('producto__nombreProducto').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')
    
    # Convertir QuerySet a diccionario Python
    ventas_por_producto = {}  # ← CREAR DICCIONARIO VACÍO
    for item in ventas_por_producto_qs:
        producto_nombre = item['producto__nombreProducto']
        cantidad_vendida = item['total_vendido']  or 0
        ventas_por_producto[producto_nombre] = cantidad_vendida
    # DATOS PARA GRÁFICA DE STOCK
    stock_data = {}
    for producto in Producto.objects.all():
        stock_data[producto.nombreProducto] = producto.stockActual
    
    # LISTA DE PRODUCTOS PARA LA TABLA
    productos = Producto.objects.all()
    
    # CONVERTIR DICCIONARIOS A JSON
    ventas_por_producto_json = json.dumps(ventas_por_producto)
    stock_data_json = json.dumps(stock_data)
    
    # CONTEXT PARA EL TEMPLATE
    context = {
        'ventas': ventas,
        'productos': productos,
        'total_ventas': total_ventas,
        'ingresos_totales': round(ingresos_totales, 2),
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'ventas_por_producto_json': ventas_por_producto_json,
        'stock_data_json': stock_data_json,
    }
    
    print("DEBUG - Ventas por producto:", ventas_por_producto)
    print("DEBUG - Stock data:", stock_data)
    
    return render(request, 'reportes/ventas.html', context)

# Función logout que falta (si no la tienes)
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('inicio')