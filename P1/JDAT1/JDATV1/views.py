from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, FloatField
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Venta
from .forms import RegistroForm, LoginForm
from .models import Usuario
from .models import MovimientoInventario
from django.contrib.auth.decorators import login_required, user_passes_test
import csv


# Registro de usuario


def registro_view(request):
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
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            correo = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, correo=correo, password=password)
            if user is not None:
                login(request, user)
                if user.rol == 'admin':
                    return redirect('inicio')  # Redirigir a la página de administración
                else:
                    return redirect('inicio')  # Redirigir a la página de usuario estándar
                
            messages.error(request, 'Correo o contraseña incorrectos.')                
    else:
        form = LoginForm()
    return render(request, 'reglog/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def es_admin(user):
    return user.rol == 'admin'

def es_empleado(user):
    return user.rol == 'empleado'
               




# INICIO PAGINA
@login_required
def inicio(request):
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
def productos (request):
    productos = Producto.objects.all()

    alertas_stock = productos.filter(stockActual__lt=5)


    return render (request, 'productos/index.html', {
        'productos': productos,
        'alertas_stock': alertas_stock
        })

    # CRUD PRODUCTOS
@login_required
def crear_producto (request):
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
def editar_producto (request, id):
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
def eliminar_producto (request, id):
    producto = Producto.objects.get(id=id)

    if request.user.rol != 'admin':
        messages.error(request, 'No tienes permiso para eliminar productos.')
        return redirect('productos')
    MovimientoInventario.objects.create(
        tipo='ELIMINAR',
        cantidad=producto.stockActual,
        idUsuario = request.user,
        idDetalle = producto,
    )
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente.')
    return redirect('productos')


#REPORTES
@login_required
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


@login_required
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
def generar_reporte(request):
        
    productos = Producto.objects.all()
    return render(request, 'reportes/generar.html', {'productos': productos})

#EXPORTAR CSV

@login_required
def exportar_csv (request):

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
            v.fecha_venta.strftime('$d/$m/%Y %H:%M')
        ])
    return response