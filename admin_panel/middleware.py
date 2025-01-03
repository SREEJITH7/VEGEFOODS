from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse



class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
###################      urls that should accessible even when blocked      ####################
        public_urls = [
            reverse('admin_login'),
            '/static/',  
            '/media/',   
        ]

################### check if the current path is public ################################

        if any(request.path.startswith(url) for url in public_urls):
            return self.get_response(request)

        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
            messages.error(request, "Your account has been blocked. Please contact support.")
            return redirect('admin_login')
            
        return self.get_response(request)