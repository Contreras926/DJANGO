from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Producto, Venta, Usuario, MovimientoInventario
from .forms import ProductoForm, RegistroForm, LoginForm
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import Sum, F, FloatField
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from functools import wraps
import csv 


# 1. SECCIÓN DE DECORADORES Y AYUDAS 

def rol_requerido(roles_permitidos):
    """Decorador maestro que verifica el rol."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login') 
            
            roles = [roles_permitidos] if isinstance(roles_permitidos, str) else roles_permitidos
            
            if request.user.rol not in roles:
                messages.error(request, ' Acceso denegado: No tienes permisos.')
                return redirect('inicio')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Atajos
admin_required = rol_requerido('admin')
empleado_required = rol_requerido('empleado')
admin_o_empleado = rol_requerido(['admin', 'empleado'])

# Registro de usuario

def registro_view(request):
    # ... código de registro ...
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'reglog/registro.html', {'form': form})

def login_view(request):
    # ... código de login ...
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            correo = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, correo=correo, password=password)
            if user is not None:
                login(request, user)
                if user.rol == 'admin':
                    return redirect('inicio') 
                else:
                    return redirect('inicio') 
                
            messages.error(request, 'Correo o contraseña incorrectos.')  
    else:
        form = LoginForm()
    return render(request, 'reglog/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

#  ELIMINADAS: Las funciones es_admin y es_empleado son obsoletas.


# INICIO PAGINA
@login_required
@admin_o_empleado # ROL APLICADO: Admin y Empleado.
def inicio(request):
    # ... lógica de la vista ...
    ventas = Venta.objects.values('producto__nombreProducto').annotate(
        total_vendido=Sum('cantidad')
    )

    ventas_por_producto = {
        V['producto__nombreProducto']: V['total_vendido'] for V in ventas
    }

    productos = Producto.objects.all()
    stock_data = {p.nombreProducto: p.stockActual for p in productos}


    return render (request, 'paginas/inicio.html',{
        'ventas_por_producto': ventas_por_producto,
        'stock_data': stock_data,
    }) 

@login_required
@admin_o_empleado # ROL APLICADO: Admin y Empleado.
def productos (request):
    # ... lógica de la vista ...
    productos = Producto.objects.all()

    alertas_stock = productos.filter(stockActual__lt=5)


    return render (request, 'productos/index.html', {
        'productos': productos,
        'alertas_stock': alertas_stock
        })

# CRUD PRODUCTOS
@login_required
@admin_required # ROL APLICADO: Solo Admin.
def crear_producto (request):
    # ... lógica de la vista ...
    formulario = ProductoForm(request.POST or None)
    
    if formulario.is_valid():
        producto = formulario.save()
        MovimientoInventario.objects.create(
            tipo='CREAR',
            cantidad=producto.stockActual,
            idUsuario = request.user,
            idDetalle = producto,
        )
        messages.success(request, 'Producto creado exitosamente.')
        return redirect('productos')
    return render (request, 'productos/crear.html',{'formulario': formulario})


@login_required
@admin_required # ROL APLICADO: Solo Admin (Faltaba este decorador).
def editar_producto (request, id):
    # ... lógica de la vista ...
    producto = Producto.objects.get(id=id)
    formulario = ProductoForm(request.POST or None, instance=producto)
    if formulario.is_valid() and request.method == 'POST':
        producto = formulario.save()
        MovimientoInventario.objects.create(
            tipo='EDITAR',
            cantidad=producto.stockActual,
            idUsuario = request.user,
            idDetalle = producto,
        )
        return redirect('productos')
    if producto.stockActual <= 5:
        messages.warning(request, 'Advertencia: El stock actual es bajo.')
    return render (request, 'productos/editar.html', {'formulario': formulario})

@login_required
@admin_required # ROL APLICADO: Solo Admin.
def eliminar_producto (request, id):
    # ... lógica de la vista ...
    producto = Producto.objects.get(id=id)
    
    MovimientoInventario.objects.create(
        tipo='ELIMINAR',
        cantidad=producto.stockActual,
        idUsuario = request.user,
        idDetalle = producto,
    )
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente.')
    return redirect('productos')


# REPORTES
@login_required
@transaction.atomic
@admin_o_empleado #  ROL APLICADO: Admin y Empleado.
def registrar_venta(request, id):
    # ... lógica de la vista ...
    producto = get_object_or_404(Producto, id=id)
    # ... lógica de venta ...
    
    return render(request, 'ventas/registrar.html', {'producto': producto})


@login_required
@admin_o_empleado
def reportes_ventas(request):
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    categoria = request.GET.get('categoria')

    categorias = Producto.objects.values_list('categoria', flat=True).distinct()

    ventas = Venta.objects.select_related('producto').all()
    
    # Aplicar filtros de fecha si existen
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
    if categoria:
        ventas = ventas.filter(producto__categoria=categoria)
    # Cálculos para reportes usando agregación
    ventas_stats = ventas.aggregate(
        total_ventas=Sum('cantidad'),
        ingresos_totales=Sum(F('cantidad') * F('precio_venta'), output_field=FloatField())
    )
    
    total_ventas = ventas_stats['total_ventas'] or 0
    ingresos_totales = ventas_stats['ingresos_totales'] or 0.0
    
    # Datos para gráfica de ventas por producto
    ventas_por_producto_qs = ventas.values('producto__nombreProducto').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')
    
    ventas_por_producto = {
        item['producto__nombreProducto']: item['total_vendido'] 
        for item in ventas_por_producto_qs
    }
    
    # Datos para gráfica de stock
    productos_stock = Producto.objects.all()
    stock_data = {
        producto.nombreProducto: producto.stockActual 
        for producto in productos_stock
    }
    
    context = {
        'ventas': ventas,
        'ventas_por_producto': ventas_por_producto,
        'stock_data': stock_data,
        'total_ventas': total_ventas,
        'ingresos_totales': round(ingresos_totales, 2),
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'categoria': categoria or '',
        'categorias': categorias,
    }
    
    return render(request, 'reportes/ventas.html', context)

@login_required
@admin_o_empleado # ROL APLICADO: Admin y Empleado (Para generar el reporte).
def generar_reporte(request):
    # ... lógica de la vista ...
    productos = Producto.objects.all()
    return render(request, 'reportes/generar.html', {'productos': productos})

@login_required
@admin_required
def exportar_csv(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    ventas = Venta.objects.select_related('producto').all()

    if fecha_inicio:
        ventas = ventas.filter(fecha_venta__date__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(fecha_venta__date__lte=fecha_fin)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'

    writer = csv.writer(response)
    writer.writerow(['Producto', 'Cantidad', 'Precio de Venta', 'Total', 'Fecha de Venta'])

    for v in ventas:
        writer.writerow([
            v.producto.nombreProducto,
            v.cantidad,
            v.precio_venta,
            v.cantidad * v.precio_venta,
            v.fecha_venta.strftime('%d/%m/%Y %H:%M') 
        ])
    return response