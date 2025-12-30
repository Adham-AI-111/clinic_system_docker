from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import logging
from django.db import connection

from django_tenants.utils import get_public_schema_name
from common.auth_utils import get_staff_tenant_for_user, get_tenant_domain, is_on_tenant_domain


logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 15
LOCKOUT_DURATION = timedelta(minutes=15)

@require_http_methods(["GET", "POST"])
def staff_login(request):
    """
    Handle login for staff members (doctors, reception, admin).
    Requires: username and password
    
    Optimized for django-tenants:
    - Authenticates user from public schema (User model is global)
    - Determines tenant from user's doctor/reception relationship
    - Redirects to tenant domain where TenantMainMiddleware handles schema switching
    - Login happens naturally on tenant domain (no manual schema_context needed)
    """
    # Check for pending login from public domain redirect
    if not request.user.is_authenticated and 'pending_staff_login' in request.session:
        pending = request.session.pop('pending_staff_login')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=pending['user_id'], username=pending['username'])
            if user.is_staff_member and not user.is_locked:
                login(request, user)
                logger.info(f"Staff login completed via redirect: {user.username}")
                messages.success(request, f'مرحباً {user.username}')
                return redirect('dashboard')
        except User.DoesNotExist:
            pass
    
    # If already authenticated and on tenant domain, redirect to dashboard
    if request.user.is_authenticated and request.user.is_staff_member:
        if is_on_tenant_domain(request):
            return redirect('dashboard')
        # If on public domain but authenticated, redirect to their tenant
        tenant = get_staff_tenant_for_user(request.user)
        if tenant:
            domain = get_tenant_domain(tenant)
            if domain:
                return redirect(f"http://{domain.domain}:8001/reception/dashboard/")

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'من فضلك أدخل اسم المستخدم وكلمة المرور')
            return render(request, 'doctor/staff_login.html')
        
        # Authenticate against public schema (User model is global)
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff_member:
            # Check if account is locked
            if user.is_locked:
                messages.error(
                    request, 
                    f'الحساب مغلق حتى {user.account_locked_until.strftime("%H:%M")}. حاول لاحقاً'
                )
                return render(request, 'doctor/staff_login.html')

            # Reset failed attempts on successful authentication
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])

            # Get tenant associated with this staff user
            tenant = get_staff_tenant_for_user(user)
            
            if not tenant:
                logger.warning(f"Staff user {user.username} (role: {user.role}) has no tenant association")
                messages.error(request, 'لا توجد عيادة مرتبطة بهذا الحساب')
                return render(request, 'doctor/staff_login.html')

            # Get primary domain for tenant
            domain = get_tenant_domain(tenant)
            if not domain:
                logger.error(f"No primary domain found for tenant: {tenant.schema_name}")
                messages.error(request, 'لا يوجد دومين مرتبط بالعيادة')
                return render(request, 'doctor/staff_login.html')

            # If we're already on the correct tenant domain, login here
            # Otherwise redirect to tenant domain first
            current_tenant = getattr(request, 'tenant', None)
            if current_tenant and current_tenant.schema_name == tenant.schema_name:
                # Already on correct tenant domain, login directly
                login(request, user)
                logger.info(f"Staff login successful on tenant domain: {user.username} ({tenant.schema_name})")
                messages.success(request, f'مرحباً {user.username}')
                return redirect('dashboard')
            else:
                # Need to redirect to tenant domain
                # Store authenticated user info in session for cross-domain login
                # This allows seamless login after redirect
                request.session['pending_staff_login'] = {
                    'user_id': user.id,
                    'username': user.username,
                }
                request.session.set_expiry(300)  # 5 minutes expiry for security
                logger.info(f"Staff authenticated, redirecting to tenant: {user.username} -> {domain.domain}")
                return redirect(f"http://{domain.domain}:8001/staff-login/")
        
        #! authenticate return none
        else:
            # Handle failed login (only increment lockout counters for staff accounts)
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(username=username)

                # Only track failed attempts for users who can legitimately use staff login
                if user.role in ['doctor', 'reception', 'admin']:
                    user.failed_login_attempts += 1
                    user.last_login_attempt = timezone.now()
                    
                    if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                        user.account_locked_until = timezone.now() + LOCKOUT_DURATION
                        user.save(update_fields=['failed_login_attempts', 'last_login_attempt', 'account_locked_until'])
                        messages.error(
                            request, 
                            f'تم غلق الحساب لمدة {LOCKOUT_DURATION.seconds // 60} دقيقة بسبب المحاولات الفاشلة'
                        )
                    else:
                        user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
                        remaining = MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
                        messages.error(request, f'بيانات خاطئة. المحاولات المتبقية: {remaining}')
                else:
                    # Non-staff accounts simply get a generic error
                    messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            except User.DoesNotExist:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            
            logger.warning(f"Failed staff login attempt for: {username}")
    
    return render(request, 'doctor/staff_login.html')


def staff_logout(request):
    """
    Logout staff user.
    Optimized for django-tenants: logout clears session regardless of schema.
    Redirects to home (tenant home if on tenant domain, public home if on public).
    """
    logout(request)
    logger.info(f"Staff logout: {request.user.username if hasattr(request, 'user') else 'anonymous'}")
    
    # Redirect to home - django-tenants middleware will handle which home to show
    return redirect('home')


