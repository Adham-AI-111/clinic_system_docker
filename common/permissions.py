from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.http import Http404

def staff_required(view_func):
    """
    Decorator to check if user has 'manager' role.
    Usage: @manager_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('home')

        # Check if user has manager role
        # if request.user.role != 'Doctor' and request.user.role != 'Reception':
        # if request.user.role not in ['doctor', 'reception']:
        if not (hasattr(request.user, 'doctor') or hasattr(request.user, 'reception')):
            raise Http404()
        
        # If all checks pass, call the original view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def doctor_required(view_func):
    """
    Decorator to check if user has 'doctor' role.
    Usage: @doctor_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('home')
        
        # Check if user has manager role
        if not hasattr(request.user, 'doctor'):
            raise PermissionDenied("doctor access required")
        
        # If all checks pass, call the original view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def user_owns_profile(view_func):
    def wrapper(request, *args, **kwargs):
        # i called the paramter by user_id because i will use the decorator with view that response user_id 
        user_id = kwargs.get('user_id')
        if not user_id or request.user.id != int(user_id) and not request.user.is_staff_member:
            raise Http404()
        return view_func(request, *args, **kwargs)
    return wrapper
