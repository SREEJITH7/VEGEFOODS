# # user/customMiddleware.py

# from django.shortcuts import redirect
# from django.urls import reverse
# # import logging

# # logger = logging.getLogger(__name__)


# class RestrictAccessMiddleware:
#     """
#     Middleware that redirects logged-out users to the login page if they try to
#     access restricted pages.
#     """

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Define URLs that require the user to be logged in
#         protected_paths = ['/welcome/']  # Add other protected URLs if needed

#         if not request.user.is_authenticated and request.path in protected_paths:
#             return redirect(reverse('login'))  # Redirect to the login page if not logged in

#         response = self.get_response(request)
#         return response




