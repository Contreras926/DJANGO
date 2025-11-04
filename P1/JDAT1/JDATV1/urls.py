from django.urls import path
from.import views

urlpatterns = [
    path ('',views.inicio, name='inicio'),
    path('nosotros', views.nosotros,name='nosotros'),
    path('productos', views.productos,name='productos'),
    path('productos/crear', views.crear_producto,name='crear_producto'),
    path('productos/editar', views.editar_producto,name='editar_producto'),
    path('eliminar/<int:id>', views.eliminar_producto,name='eliminar_producto'),
    path('editar/<int:id>', views.editar_producto, name='editar_producto'), 
    path('logout/', views.logout, name='logout'),
    path('signin/', views.signin, name='signin')
]