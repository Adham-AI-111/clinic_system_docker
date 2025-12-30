from django import forms
from django.forms import widgets
from .models import User, Doctor


class UserSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'phone', 'password',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'الاسم'
        self.fields['phone'].label = 'رقم الهاتف'
        # self.fields['role'].label = 'التصنيف'
        self.fields['password'].label = 'الرقم السري'
