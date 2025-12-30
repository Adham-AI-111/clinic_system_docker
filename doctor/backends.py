
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class StaffAuthBackend(ModelBackend):
    """
    Authentication backend for staff members (doctors, reception, admin).
    Staff login using username + password.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Support login with username OR email
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            User().set_password(password)
            logger.warning(f"Failed staff login attempt for username: {username}")
            return None
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple users found for: {username}")
            return None
        
        # Check password
        if not user.check_password(password):
            logger.warning(f"Invalid password for user: {username}")
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {username}")
            return None
        
        # Verify user is staff (doctor, reception, or admin)
        if user.role not in ['doctor', 'reception', 'admin']:
            logger.warning(f"Non-staff user tried staff login: {username} (role: {user.role})")
            return None
        
        logger.info(f"Successful staff login: {username} (role: {user.role})")
        return user


class PatientAuthBackend(ModelBackend):
    """
    Authentication backend for patients.
    Patients login using phone number + username (no password required).
    """
    
    def authenticate(self, request, phone=None, username=None, **kwargs):
        if phone is None or username is None:
            return None
        
        # Normalize phone - PhoneNumberField handles this, but be safe
        phone_str = str(phone).strip()
        
        try:
            # Fetch user by both phone AND username AND role
            user = User.objects.get(
                phone=phone_str,
                username=username,
                role='patient'
            )
        except User.DoesNotExist:
            logger.warning(f"Failed patient login - phone: {phone_str}, username: {username}")
            return None
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple patients found - phone: {phone_str}, username: {username}")
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive patient login attempt: {username}")
            return None
        
        # Additional security check
        if user.role != 'patient':
            logger.error(f"Role mismatch in patient login: {username} has role {user.role}")
            return None
        
        logger.info(f"Successful patient login: {username}, phone: {phone_str}")
        return user