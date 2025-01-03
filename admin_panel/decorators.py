from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Check if the user is authenticated and is an admin ie is_staff is true
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            
            return redirect('admin_login')
    return wrapper




