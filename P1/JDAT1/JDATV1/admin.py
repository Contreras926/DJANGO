from django.contrib import admin
from .models import Producto, Venta

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombreProducto', 'categoria', 'preciolmitario', 'stockActual', 'stockMinimo']  # ← MANTIENE preciolmitario
    list_filter = ['categoria']
    search_fields = ['nombreProducto']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'precio_venta', 'fecha_venta']
    list_filter = ['fecha_venta', 'producto__categoria']
    date_hierarchy = 'fecha_venta'