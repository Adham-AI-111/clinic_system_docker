from datetime import timedelta
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django_tenants.utils import get_public_schema_name
from django.db import connection

from common.permissions import staff_required
from common.auth_utils import is_on_tenant_domain, guard_public_schema

from .forms import PatientSignupForm


logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 15
LOCKOUT_DURATION = timedelta(minutes=15)


@staff_required
def signup_patient(request):
    if request.method == 'POST':
        form = PatientSignupForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PatientSignupForm(request=request)

    context = {'form':form}
    return render(request, 'reception/add_patient.html', context)



@require_http_methods(["GET", "POST"])
def patient_login(request):
    """
    Handle login for patients.
    Requires: phone and username (no password)
    
    Optimized for django-tenants (Option A - simpler):
    - Patients MUST login from clinic domain (tenant domain)
    - Tenant is determined from request.tenant (current domain)
    - Patient data (Patient model) exists only in tenant schema
    - Login happens on tenant domain where Patient model is accessible
    """
    # Guard: Patients should only login from tenant domains, not public
    public_guard = guard_public_schema(request, redirect_view='home')
    if public_guard:
        return public_guard
    
    if request.user.is_authenticated:
        return redirect('patient-profile', user_id=request.user.id)

    # Get tenant from current request (we're on tenant domain)
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'يجب الوصول من خلال دومين العيادة')
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        
        if not phone or not username:
            messages.error(request, 'من فضلك أدخل رقم الهاتف واسم المستخدم')
            return render(request, 'patient/patient_login.html')
        
        # Authenticate against public schema (User model is global)
        user = authenticate(request, phone=phone, username=username)
        
        if user is not None:
            # Check if account is locked
            if user.is_locked:
                messages.error(request, 'الحساب مغلق. تواصل مع الاستقبال')
                return render(request, 'patient/patient_login.html')
            
            # Reset failed attempts on successful auth
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            
            # Verify patient exists in current tenant schema
            # We're already in tenant schema context (TenantMainMiddleware)
            try:
                from patient.models import Patient
                patient = Patient.objects.get(user=user)
                
                # Patient exists in this tenant, login successful
                login(request, user)
                messages.success(request, f'مرحباً {user.username}')
                logger.info(f"Patient login successful: {user.username}-{user.id} (tenant: {tenant.schema_name})")
                return redirect('patient-profile', user_id=user.id)
                
            except Patient.DoesNotExist:
                # Patient doesn't exist in this tenant schema
                messages.error(request, 'لا يوجد ملف مريض مرتبط بهذا الحساب في هذه العيادة')
                logger.warning(f"Patient {user.username} tried to login but no Patient record in tenant {tenant.schema_name}")
                return render(request, 'patient/patient_login.html')
        
        # Handle failed login attempts
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(phone=phone, username=username)
            
            user.failed_login_attempts += 1
            user.last_login_attempt = timezone.now()
            
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.account_locked_until = timezone.now() + LOCKOUT_DURATION
                user.save(update_fields=['failed_login_attempts', 'last_login_attempt', 'account_locked_until'])
                messages.error(request, 'تم غلق الحساب. تواصل مع الاستقبال')
            else:
                user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
                messages.error(request, 'رقم الهاتف أو اسم المستخدم غير صحيح')
        except User.DoesNotExist:
            messages.error(request, 'رقم الهاتف أو اسم المستخدم غير صحيح')
        
        logger.warning(f"Failed patient login - phone: {phone}, username: {username}")
    
    return render(request, 'patient/patient_login.html')


def patient_logout(request):
    """
    Logout patient user.
    Optimized for django-tenants: logout clears session regardless of schema.
    Redirects to patient login page on same tenant domain.
    """
    logout(request)
    logger.info(f"Patient logout: {request.user.username if hasattr(request, 'user') else 'anonymous'}")
    
    # Redirect to patient login on same tenant domain
    return redirect('patient-login')

 