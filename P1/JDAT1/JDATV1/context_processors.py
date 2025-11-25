def roles_context(request):
    """
    Inyecta variables booleanas 'is_admin' y 'is_empleado' en los templates.
    """
    if request.user.is_authenticated:
        # Usamos .get() por seguridad si el campo 'rol' no existe por alguna razón
        user_rol = getattr(request.user, 'rol', None) 
        return {
            'is_admin': user_rol == 'admin',    
            'is_empleado': user_rol == 'empleado', 
            'user_role': user_rol
        }
    return {
        'is_admin': False, 
        'is_empleado': False,
        'user_role': None
    }