# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from patient.models import Appointment
# from reception.views import invalidate_dashboard_cache


# @receiver(post_save, sender=Appointment)
# def invalidate_cache_on_appointment_change(sender, instance, created, **kwargs):
#     """Automatically invalidate cache when appointment is created or updated"""
#     try:
#         tenant_id = instance.patient.user.doctor.id
#         action = "created" if created else "updated"
#         invalidate_dashboard_cache(tenant_id)
#         print(f"✓ Appointment {instance.id} {action} - cache auto-invalidated")
#     except Exception as e:
#         print(f"✗ Error auto-invalidating cache on save: {e}")


# @receiver(post_delete, sender=Appointment)
# def invalidate_cache_on_appointment_delete(sender, instance, **kwargs):
#     """Automatically invalidate cache when appointment is deleted"""
#     try:
#         tenant_id = instance.patient.user.doctor.id
#         invalidate_dashboard_cache(tenant_id)
#         print(f"✓ Appointment {instance.id} deleted - cache auto-invalidated")
#     except Exception as e:
#         print(f"✗ Error auto-invalidating cache on delete: {e}")
