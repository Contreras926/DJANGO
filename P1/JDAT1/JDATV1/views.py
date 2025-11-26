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


# ========================================
# 1. SECCIÓN DE DECORADORES Y AYUDAS 
# ========================================

def rol_requerido(roles_permitidos):
    """
    Decorador maestro que verifica el rol del usuario autenticado.
    
    Args:
        roles_permitidos: String con un rol ('admin') o lista de roles (['admin', 'empleado'])
    
    Returns:
        Decorator function que verifica autenticación y rol antes de ejecutar la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder.')
                return redirect('login') 
            
            # Normalizar roles_permitidos a lista
            roles = [roles_permitidos] if isinstance(roles_permitidos, str) else roles_permitidos
            
            # Verificar si el usuario tiene el rol requerido
            if request.user.rol not in roles:
                messages.error(request, 'Acceso denegado: No tienes permisos para esta acción.')
                return redirect('inicio')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Atajos de decoradores
admin_required = rol_requerido('admin')
empleado_required = rol_requerido('empleado')
admin_o_empleado = rol_requerido(['admin', 'empleado'])


# ========================================
# 2. AUTENTICACIÓN Y REGISTRO
# ========================================

def registro_view(request):
    """Vista pública para registro de nuevos usuarios"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    return render(request, 'reglog/registro.html', {'form': form})


def login_view(request):
    """Vista pública para inicio de sesión"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            correo = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Autenticar usando el campo correo
            user = authenticate(request, correo=correo, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido, {user.nombreUsuario}!')
                return redirect('inicio')
            else:
                messages.error(request, 'Correo o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor verifica tus credenciales.')
    else:
        form = LoginForm()
    return render(request, 'reglog/login.html', {'form': form})


def logout_view(request):
    """Vista pública para cerrar sesión"""
    nombre = request.user.nombreUsuario if request.user.is_authenticated else ""
    logout(request)
    if nombre:
        messages.info(request, f'Hasta luego, {nombre}. Sesión cerrada exitosamente.')
    else:
        messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('login')


# ========================================
# 3. PÁGINA DE INICIO (Dashboard)
# ========================================

@login_required
@admin_o_empleado
def inicio(request):
    """Dashboard principal - Accesible para Admin y Empleado"""
    ventas = Venta.objects.values('producto__nombreProducto').annotate(
        total_vendido=Sum('cantidad')
    )

    ventas_por_producto = {
        v['producto__nombreProducto']: v['total_vendido'] for v in ventas
    }

    productos = Producto.objects.all()
    stock_data = {p.nombreProducto: p.stockActual for p in productos}

    return render(request, 'paginas/inicio.html', {
        'ventas_por_producto': ventas_por_producto,
        'stock_data': stock_data,
    })


# ========================================
# 4. LISTADO DE PRODUCTOS
# ========================================

@login_required
@admin_o_empleado
def productos(request):
    """Listado de productos - Accesible para Admin y Empleado"""
    productos = Producto.objects.all()
    alertas_stock = productos.filter(stockActual__lt=5)

    return render(request, 'productos/index.html', {
        'productos': productos,
        'alertas_stock': alertas_stock
    })


# ========================================
# 5. CRUD DE PRODUCTOS (SOLO ADMIN)
# ========================================

@login_required
@admin_required
def crear_producto(request):
    """Crear producto - SOLO ADMIN"""
    formulario = ProductoForm(request.POST or None)
    
    if formulario.is_valid():
        producto = formulario.save()
        
        # Registrar movimiento de inventario
        MovimientoInventario.objects.create(
            tipo='CREAR',
            cantidad=producto.stockActual,
            idUsuario=request.user,
            idDetalle=producto,
        )
        
        messages.success(request, f'Producto "{producto.nombreProducto}" creado exitosamente.')
        return redirect('productos')
    
    return render(request, 'productos/crear.html', {'formulario': formulario})


@login_required
@admin_required
def editar_producto(request, id):
    """Editar producto - SOLO ADMIN"""
    producto = get_object_or_404(Producto, id=id)
    formulario = ProductoForm(request.POST or None, instance=producto)
    
    if formulario.is_valid() and request.method == 'POST':
        producto = formulario.save()
        
        # Registrar movimiento de inventario
        MovimientoInventario.objects.create(
            tipo='EDITAR',
            cantidad=producto.stockActual,
            idUsuario=request.user,
            idDetalle=producto,
        )
        
        messages.success(request, f'Producto "{producto.nombreProducto}" actualizado exitosamente.')
        return redirect('productos')
    
    # Advertencia si el stock es bajo
    if producto.stockActual <= 5:
        messages.warning(request, f'Advertencia: El stock actual de "{producto.nombreProducto}" es bajo ({producto.stockActual} unidades).')
    
    return render(request, 'productos/editar.html', {'formulario': formulario})


@login_required
@admin_required
def eliminar_producto(request, id):
    """Eliminar producto - SOLO ADMIN"""
    producto = get_object_or_404(Producto, id=id)
    nombre_producto = producto.nombreProducto
    
    # Registrar movimiento antes de eliminar
    MovimientoInventario.objects.create(
        tipo='ELIMINAR',
        cantidad=producto.stockActual,
        idUsuario=request.user,
        idDetalle=producto,
    )
    
    producto.delete()
    messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
    return redirect('productos')


# ========================================
# 6. VENTAS Y REPORTES
# ========================================

@login_required
@transaction.atomic
@admin_o_empleado
def registrar_venta(request, id):
    """Registrar venta de un producto - Admin y Empleado"""
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 0))
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido.')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        # Validaciones
        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        if cantidad > producto.stockActual:
            messages.error(request, f'Stock insuficiente. Solo hay {producto.stockActual} unidades disponibles.')
            return render(request, 'ventas/registrar.html', {'producto': producto})
        
        # Registrar venta
        Venta.objects.create(
            producto=producto,
            cantidad=cantidad,
            precio_venta=producto.precioUnitario
        )
        
        # Actualizar stock
        producto.stockActual -= cantidad
        producto.save()
        
        total_venta = cantidad * producto.precioUnitario
        messages.success(request, f'Venta registrada: {cantidad} unidades de {producto.nombreProducto}. Total: ${total_venta}')
        return redirect('productos')
    
    return render(request, 'ventas/registrar.html', {'producto': producto})


@login_required
@admin_o_empleado
def reportes_ventas(request):
    """Vista de reportes de ventas con filtros - Admin y Empleado"""
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    categoria = request.GET.get('categoria')

    categorias = Producto.objects.values_list('categoria', flat=True).distinct()
    ventas = Venta.objects.select_related('producto').all()
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            ventas = ventas.filter(fecha_venta__date__gte=fecha_inicio_dt)
        except ValueError:
            messages.warning(request, 'Formato de fecha de inicio inválido.')
            fecha_inicio = None
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            ventas = ventas.filter(fecha_venta__date__lte=fecha_fin_dt)
        except ValueError:
            messages.warning(request, 'Formato de fecha fin inválido.')
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
@admin_o_empleado
def generar_reporte(request):
    """Página de generación de reportes - Admin y Empleado"""
    productos = Producto.objects.all()
    return render(request, 'reportes/generar.html', {'productos': productos})


@login_required
@admin_required
def exportar_csv(request):
    """Exportar reporte a CSV - SOLO ADMIN"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    ventas = Venta.objects.select_related('producto').all()

    if fecha_inicio:
        try:
            ventas = ventas.filter(fecha_venta__date__gte=fecha_inicio)
        except:
            messages.error(request, 'Fecha de inicio inválida.')
            return redirect('reportes_ventas')
            
    if fecha_fin:
        try:
            ventas = ventas.filter(fecha_venta__date__lte=fecha_fin)
        except:
            messages.error(request, 'Fecha fin inválida.')
            return redirect('reportes_ventas')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'
    
    # BOM para UTF-8 (para que Excel abra correctamente los acentos)
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Producto', 'Cantidad', 'Precio de Venta', 'Total', 'Fecha de Venta'])

    for v in ventas:
        writer.writerow([
            v.producto.nombreProducto,
            v.cantidad,
            f'${v.precio_venta}',
            f'${v.cantidad * v.precio_venta}',
            v.fecha_venta.strftime('%d/%m/%Y %H:%M') 
        ])
    
    messages.success(request, f'Reporte CSV generado con {ventas.count()} registros.')
    return response