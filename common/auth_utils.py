"""
Shared authentication utilities for multi-tenant clinic system.
Compatible with django-tenants architecture.
"""
from django.db import connection
from django_tenants.utils import get_public_schema_name
from doctor.models import Domain


def get_staff_tenant_for_user(user):
    """
    Get the tenant (Doctor) associated with a staff user.
    Returns None if user is not staff or has no tenant association.
    
    Args:
        user: User instance (must be staff member)
    
    Returns:
        Doctor instance or None
    """
    if hasattr(user, 'doctor'):
        return user.doctor
    elif hasattr(user, 'reception'):
        return user.reception.doctor
    return None


def get_tenant_domain(tenant):
    """
    Get the primary domain for a tenant.
    
    Args:
        tenant: Doctor instance
    
    Returns:
        Domain instance or None
    """
    if not tenant:
        return None
    return Domain.objects.filter(tenant=tenant, is_primary=True).first()


def guard_public_schema(request, redirect_view='home'):
    """
    Guard function to prevent accessing tenant-only views from public schema.
    Returns redirect response if on public schema, None otherwise.
    
    Args:
        request: Django request object
        redirect_view: Name of view to redirect to (default: 'home')
    
    Returns:
        HttpResponseRedirect if on public schema, None otherwise
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    
    if connection.schema_name == get_public_schema_name():
        messages.error(request, 'يجب الوصول من خلال دومين العيادة')
        return redirect(redirect_view)
    return None


def is_on_tenant_domain(request):
    """
    Check if request is on a tenant domain (not public).
    
    Args:
        request: Django request object
    
    Returns:
        bool: True if on tenant domain, False if on public
    """
    return connection.schema_name != get_public_schema_name()

