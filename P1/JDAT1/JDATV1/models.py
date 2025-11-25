from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, nombreUsuario, apellidoUsuario, rol, password=None):
        if not correo:
            raise ValueError('El email debe ser proporcionado')
        
        usuario = self.model(
            correo=self.normalize_email(correo),
            nombreUsuario=nombreUsuario,
            apellidoUsuario=apellidoUsuario,
            rol=rol
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario
    def create_superuser(self, correo, nombreUsuario, apellidoUsuario, password):
        usuario = self.create_user(
            correo,
            nombreUsuario=nombreUsuario,
            apellidoUsuario=apellidoUsuario,
            rol='admin',
            password=password
        )
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario
    
ROLES = [
    ('admin', 'Administrador'),
    ('empleado', 'Empleado'),
]

class Usuario(AbstractBaseUser, PermissionsMixin):
    nombreUsuario = models.CharField(verbose_name="Nombre", max_length=100)
    apellidoUsuario = models.CharField(verbose_name="Apellido", max_length=100)
    correo = models.EmailField(verbose_name="Correo", max_length=255, unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='empleado', verbose_name="Rol del Usuario")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombreUsuario', 'apellidoUsuario']

    def __str__(self):
        return F"{self.nombreUsuario} {self.apellidoUsuario}"
    
class MovimientoInventario(models.Model):
    TIPOS_MOVIMIENTO = [
        ('CREAR', 'Creación'),
        ('EDITAR', 'Edición'),  
        ('ELIMINAR', 'Eliminación'),
    ]

    idMovimiento = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPOS_MOVIMIENTO)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField(verbose_name="Cantidad/Stock")

    idUsuario = models.ForeignKey(
        'Usuario', 
        on_delete=models.CASCADE, 
        verbose_name="Usuario que realiza el movimiento"
        )
    
    idDetalle = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name="Producto afectado"
        )
    def __str__(self):
        return f"{self.tipo} - {self.idDetalle.nombreProducto} - {self.fecha}"