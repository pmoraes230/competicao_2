from django.shortcuts import redirect
from django.urls import reverse
from musichall.views import get_user_profile

class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        public_urls = [reverse('login'), reverse('logout')]
        context = get_user_profile(request)
        is_authenticated = context.get('is_authenticated', False)
        
        if is_authenticated and request.path == reverse('login'):
            return redirect('home')
        if not is_authenticated and request.path not in public_urls:
            return redirect('login')
        
        response = self.get_response(request)
        return response