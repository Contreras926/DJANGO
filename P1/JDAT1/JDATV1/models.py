from django.db import models

# Create your models here.
class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombreProducto = models.CharField(max_length=100, verbose_name="Nombre del Producto")
    descripcion = models.CharField(max_length=200, verbose_name="Descripción del Producto")
    CATEGORIAS = [
        ('Lacteos', 'Lacteos'),
        ('Embutidos', 'Embutidos'),
        ('Salsas', 'Salsas'),
        ('Bebidas', 'Bebidas'),
    ]
    categoria = models.CharField(max_length=100, choices=CATEGORIAS,verbose_name="Categoría del Producto")
    precioUnitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    stockMinimo = models.IntegerField(verbose_name="Stock Mínimo")
    stockActual = models.IntegerField(verbose_name="Stock Actual")
def __str__(self):
        return self.nombreProducto

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombreUsuario = models.CharField(max_length=100, verbose_name="Nombre de Usuario")
    apellidoUsuario = models.CharField(max_length=100, verbose_name="Apellido de Usuario")
    contrasena = models.CharField(max_length=100, verbose_name="Contraseña")
    rol = models.CharField(max_length=50, verbose_name="Rol del Usuario")
    correo = models.EmailField(verbose_name="Correo Electrónico")

class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete = models.CASCADE, verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad Vendida")
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta")
    
    def __str__(self):
        return f"{self.producto.nombreProducto} - {self.cantidad} unidades"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"