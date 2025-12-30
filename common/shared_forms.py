from django import forms
from patient.models import Appointment


# i set it in commoc app, while its view in doctor app, because in future i will let patient book an appointment by himself
class CreateAppointmentForm(forms.ModelForm):
    next_url = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Appointment
        fields = ['date', 'status', 'is_prior']
        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'status': forms.Select(attrs={'class':'choice-box'}),
        }

    def __init__(self, *args, **kwargs):
        '''
        1. get the patient using the dynamic url
        2. pass patient instanse from patient_profile view
        3. set the relation between patient and appointment in save method
        '''
        self.patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if self.patient:
            appointment.patient = self.patient
        
        if commit:
            appointment.save()
        return appointment