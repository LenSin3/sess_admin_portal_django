# Create a new file called context_processors.py in your app directory

def user_profile(request):
    """Context processor to add profile picture to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            # Make sure employee is available
            employee = request.user.employee
            context['employee'] = employee
        except:
            pass
            
    return context