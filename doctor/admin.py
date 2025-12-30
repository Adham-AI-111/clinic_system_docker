from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Doctor, User, Domain

admin.site.register(User)

@admin.register(Doctor)
class DoctorAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = ('major',)

@admin.register(Domain)
class DomainAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = ('domain', 'tenant', 'is_primary')