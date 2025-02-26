from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Middleware to redirect unauthenticated users to the login page
    for all URLs except those in the exempted list.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # List of URLs that don't require authentication
        self.exempt_urls = [
            reverse('login'),
            # Add any other exempt URLs here
        ]
    
    def __call__(self, request):
        # If user is not authenticated and trying to access a protected URL
        if not request.user.is_authenticated:
            current_path = request.path_info
            
            # Check if the current path is exempt
            if current_path not in self.exempt_urls:
                # Check for static files and other exempt paths
                if not current_path.startswith(settings.STATIC_URL) and not current_path.startswith('/admin/'):
                    # Redirect to login page with the next parameter
                    return redirect(f"{reverse('login')}?next={current_path}")
        
        response = self.get_response(request)
        return response