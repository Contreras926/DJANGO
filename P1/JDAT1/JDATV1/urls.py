from django.urls import path
from.import views

urlpatterns = [
    path ('',views.inicio, name='inicio'),
    path('productos', views.productos,name='productos'),
    path('productos/crear', views.crear_producto,name='crear_producto'),
    path('productos/editar', views.editar_producto,name='editar_producto'),
    path('eliminar/<int:id>', views.eliminar_producto,name='eliminar_producto'),
    path('editar/<int:id>', views.editar_producto, name='editar_producto'), 
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    
    path('ventas/registrar/<int:id>', views.registrar_venta, name='registrar_venta'),
    path('reportes/ventas', views.reportes_ventas, name='reportes_ventas'),
    path('paginas/logout/', views.logout_view, name='logout'),
    path('reportes/generar/', views.generar_reporte, name='generar_reporte'),
]