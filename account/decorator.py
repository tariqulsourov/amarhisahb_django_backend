from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def admin_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        user_type = request.user.user_type.user_type
        if user_type== 'admin':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
            
    return wrapper_function

def regular_user_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        user_type = request.user.user_type.user_type
        if user_type== 'regular_user':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
            
    return wrapper_function


