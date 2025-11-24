from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto, Venta
from .forms import ProductoForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, FloatField
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction

# Importaciones de Plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot


# Create your views here.

def inicio(request):
    return render(request, 'paginas/inicio.html') 

def nosotros(request):
    return render(request, 'paginas/nosotros.html')     

def productos(request):
    productos = Producto.objects.all()
    return render(request, 'productos/index.html', {'productos': productos})

def crear_producto(request):
    formulario = ProductoForm(request.POST or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('productos')
    return render(request, 'productos/crear.html', {'formulario': formulario})

def editar_producto(request, id):
    producto = Producto.objects.get(id=id)
    formulario = ProductoForm(request.POST or None, instance=producto)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('productos')
    return render(request, 'productos/editar.html', {'formulario': formulario})

def eliminar_producto(request, id):
    libro = Producto.objects.get(id=id)
    libro.delete()
    return redirect('productos')

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
        
        producto = Producto.objects.select_for_update().get(id=id)
        
        if cantidad > producto.stockActual:
            messages.error(request, f'Stock insuficiente. Stock actual: {producto.stockActual}')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        Venta.objects.create(
            producto=producto,
            cantidad=cantidad,
            precio_venta=producto.precioUnitario
        )
        
        producto.stockActual -= cantidad
        producto.save()
        
        messages.success(request, f'Venta registrada: {cantidad} unidades de {producto.nombreProducto}')
        return redirect('productos')
    
    return render(request, 'ventas/registrar.html', {'producto': producto})


# FUNCIONES GENERADORAS DE GRÁFICAS PLOTLY

def generar_grafica_ventas_plotly(ventas_por_producto):
    """
    Genera gráfica de barras interactiva con Plotly
    
    Args:
        ventas_por_producto (dict): {nombre_producto: cantidad}
    
    Returns:
        str: HTML embebible de la gráfica
    """
    if not ventas_por_producto:
        return '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> No hay ventas registradas para mostrar.</div>'
    
    productos = list(ventas_por_producto.keys())
    cantidades = list(ventas_por_producto.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=productos,
            y=cantidades,
            marker=dict(
                color=cantidades,
                colorscale='Blues',
                line=dict(color='rgb(8,48,107)', width=2)
            ),
            text=cantidades,
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Unidades: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title={
            'text': 'Productos Más Vendidos',
            'font': {'size': 20, 'family': 'Arial, sans-serif', 'color': '#2c3e50'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title='Productos',
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(
            title='Unidades Vendidas',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=80, b=100),
        height=400,
        hovermode='x unified'
    )
    
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'responsive': True
    }
    
    # CORREGIDO: include_plotlyjs=False
    plot_html = plot(fig, output_type='div', include_plotlyjs=False, config=config)
    return plot_html


def generar_grafica_stock_plotly(stock_data):
    """
    Genera gráfica circular interactiva con Plotly
    
    Args:
        stock_data (dict): {nombre_producto: cantidad_stock}
    
    Returns:
        str: HTML embebible de la gráfica
    """
    if not stock_data:
        return '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> No hay productos para mostrar.</div>'
    
    productos = list(stock_data.keys())
    cantidades = list(stock_data.values())
    
    fig = go.Figure(data=[
        go.Pie(
            labels=productos,
            values=cantidades,
            hole=0.3,
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textposition='inside',
            hovertemplate='<b>%{label}</b><br>Stock: %{value}<br>%{percent}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title={
            'text': 'Distribución de Inventario',
            'font': {'size': 18, 'family': 'Arial, sans-serif', 'color': '#2c3e50'},
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=80, b=80),
        height=400
    )
    
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'responsive': True
    }
    
    #  CORREGIDO: include_plotlyjs=False
    plot_html = plot(fig, output_type='div', include_plotlyjs=False, config=config)
    return plot_html


def reportes_ventas(request):
    """
    Vista de reportes con gráficas Plotly
    """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    ventas = Venta.objects.select_related('producto').all()

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
    
    ventas_stats = ventas.aggregate(
        total_ventas=Sum('cantidad'),
        ingresos_totales=Sum(F('cantidad') * F('precio_venta'), output_field=FloatField())
    )
    
    total_ventas = ventas_stats['total_ventas'] or 0
    ingresos_totales = ventas_stats['ingresos_totales'] or 0.0
    
    ventas_por_producto_qs = ventas.values('producto__nombreProducto').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')
    
    ventas_por_producto = {}
    for item in ventas_por_producto_qs:
        producto_nombre = item['producto__nombreProducto']
        cantidad_vendida = item['total_vendido'] or 0
        ventas_por_producto[producto_nombre] = cantidad_vendida
    
    stock_data = {}
    for producto in Producto.objects.all():
        stock_data[producto.nombreProducto] = producto.stockActual
    
    productos = Producto.objects.all()
    
    # Generar gráficas con Plotly
    grafica_ventas_html = generar_grafica_ventas_plotly(ventas_por_producto)
    grafica_stock_html = generar_grafica_stock_plotly(stock_data)
    
    context = {
        'ventas': ventas,
        'productos': productos,
        'total_ventas': total_ventas,
        'ingresos_totales': round(ingresos_totales, 2),
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'grafica_ventas': grafica_ventas_html,
        'grafica_stock': grafica_stock_html,
    }
    
    print("DEBUG - Ventas por producto:", ventas_por_producto)
    print("DEBUG - Stock data:", stock_data)
    
    return render(request, 'reportes/ventas.html', context)


def logout_view(request):
    logout(request)
    return redirect('inicio')