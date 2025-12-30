from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from doctor.models import User, Doctor
from django.utils import timezone
from django.core.exceptions import ValidationError

# TODO: add ability to access the current tenant here
# def get_current_doctor():
#     from django_tenants.utils import get_tenant_model, get_current_schema_name
#     return get_tenant_model().objects.get(schema_name=get_current_schema_name())


class Patient(models.Model):
    #TODO: use username field from main User model
    # name = models.CharField(max_length=30)
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # max digit
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patients')
    # doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.username


class Appointment(models.Model):
    APPOINT_STATUS = [('Completed', 'Completed'), ('Pending', 'Pending'), ('Canceled', 'Canceled')]
    # i will use this field to handle the appointments date operation like order matter in home page
    date = models.DateField()
    cost = models.IntegerField(
    validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=12, choices=APPOINT_STATUS, default='Pending')
    is_prior = models.BooleanField(default=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # the newest first
    
    def __str__(self):
        return f"{self.date} - {self.status} for user {self.patient.user.username}"
    
    def clean(self):
        if self.date < timezone.now().date():
            raise ValidationError("Appointment cannot be in the past.")

    @property
    def status_class(self):
        # used in htmx for update the apppoint status in main dashboard, to exchange the css class  
        return {
            'Completed': 'success',
            'Pending': 'warning',
            'Canceled': 'danger',
        }.get(self.status, 'secondary')


class Diagnosis(models.Model):
    diagnosis = models.TextField(max_length=200)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.diagnosis[:10]


class Prescription(models.Model):
    prescription = models.TextField(max_length=100)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Requires(models.Model):
    requires = models.TextField(max_length=100)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
