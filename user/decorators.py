from django.shortcuts import redirect 
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpResponseForbidden


def login_required(view_func):

    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view






def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Check if the user is authenticated and NOT an admin (is_staff is False)
        if request.user.is_authenticated and not request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            # Return an HTTP 403 Forbidden response or render a custom error page
            return HttpResponseForbidden("You do not have permission to access this page.")
    return wrapper