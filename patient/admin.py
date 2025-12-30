from django.contrib import admin
from .models import Patient, Appointment, Diagnosis, Prescription

admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Diagnosis)
admin.site.register(Prescription)
