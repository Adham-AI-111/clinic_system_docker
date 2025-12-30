from django.db import models
from doctor.models import User, Doctor

class Reception(models.Model):
    #TODO: user username field in main user model
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    # doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username
