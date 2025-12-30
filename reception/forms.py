from django import forms
from doctor.models import User, Doctor
from .models import Reception
from doctor.forms import UserSignupForm

class ReceptionProfileForm(forms.ModelForm):
    class Meta:
        model = Reception
        fields = []

class ReceptionSignupForm(UserSignupForm):
    def __init__(self, *args, **kwargs):
        # allow us to use "request" in save method
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # create PatientProfileForm instance to use its fields
        self.reception_form = ReceptionProfileForm(data=self.data if self.is_bound else None,
            prefix='reception')

        #!  "combinaton fields here"  Merge fields into this form
        self.fields.update(self.reception_form.fields)
        
    def is_valid(self):
        return super().is_valid() and self.reception_form.is_valid()

    def save(self, commit=True):
        if not self.request:
            raise ValueError("Request must be passed to ReceptionSignupForm")

        # save user directly by commit=true, beacuse no more actions we want to do on user model
        # if not saved the teacher will not created, because the relation will faild
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
    
        # set the relations
        reception = self.reception_form.save(commit=False) # this work on Reception model through the ModelForm
        reception.user = user
        reception.user.role = 'reception'
        # reception.doctor = self.request.tenant
        reception.save()
        return user