from django.urls import path
from.import views
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login'), name='root'),
    

    path ('paginas/inicio.html',views.inicio, name='inicio'),
    path('productos', views.productos,name='productos'),
    path('productos/crear', views.crear_producto,name='crear_producto'),
    path('productos/editar', views.editar_producto,name='editar_producto'),
    path('eliminar/<int:id>', views.eliminar_producto,name='eliminar_producto'),
    path('editar/<int:id>', views.editar_producto, name='editar_producto'), 
    
    path('reglog/registro/', views.registro_view, name='registro'),
    path('reglog/login/', views.login_view, name='login'),
    path('reglog/logout/', views.logout_view, name='logout'),
    
    path('ventas/registrar/<int:id>', views.registrar_venta, name='registrar_venta'),
    path('reportes/ventas', views.reportes_ventas, name='reportes_ventas'),
    path('reportes/generar/', views.generar_reporte, name='generar_reporte'),
]