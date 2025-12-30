from django import forms
from doctor.models import User, Doctor
from .models import Patient, Appointment, Diagnosis, Prescription, Requires
from doctor.forms import UserSignupForm

# used in concat between user model and patient model
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['age']
        widgets = {
            'age': forms.NumberInput(attrs={'type': 'number'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['age'].label = 'العمر'


class PatientSignupForm(UserSignupForm):
    '''
    compination between user model and patient model to create patint user
    '''
    DEFAULT_PASSWORD = 'patient123'
    
    # Override password field to be optional with default value
    password = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial=DEFAULT_PASSWORD
    )
    
    def __init__(self, *args, **kwargs):
        # allow us to use "request" in save method
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Remove password label since it's hidden
        self.fields['password'].label = ''

        # create PatientProfileForm instance to use its fields
        self.patient_form = PatientProfileForm(data=self.data if self.is_bound else None)

        #!  "combinaton fields here"  Merge fields into this form
        self.fields.update(self.patient_form.fields)

    def is_valid(self):
        return super().is_valid() and self.patient_form.is_valid()

    def save(self, commit=True):
        if not self.request:
            raise ValueError("Request must be passed to PatientSignupForm")

        # save user directly by commit=true, beacuse no more actions we want to do on user model
        user = super().save(commit=False)
        
        # Use default password if not provided
        password = self.cleaned_data.get('password') or self.DEFAULT_PASSWORD
        user.set_password(password)
        
        if commit: # the default commit
            user.save()

        # set the relations
        patient = self.patient_form.save(commit=False)
        patient.user = user
        patient.user.role = 'patient'
        # In django-tenants, the Doctor model represents the tenant itself.
        # After removing the ForeignKey/OneToOne relationship between Patient and Doctor,
        # the association is no longer stored as a database field.
        #  --->
        # The link between Patient and Doctor is now implicit via the tenant schema.
        #! patient.doctor = self.request.tenant
        patient.save()
        # TODO: how commit work in view in this case, if type commit=false in view
        return user


class CreateDiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ['diagnosis']

    def __init__(self, *args, **kwargs):
        # pass appointment to form parameters
        self.appointment = kwargs.pop('appointment', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        diagnosis = super().save(commit=False)

        diagnosis.appointment = self.appointment
        if commit:
            diagnosis.save()

        return diagnosis


class CreatePrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['prescription']

    def __init__(self, *args, **kwargs):
        # pass appointment to form parameters
        self.appointment = kwargs.pop('appointment', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        prescription = super().save(commit=False)

        prescription.appointment = self.appointment
        if commit:
            prescription.save()

        return prescription


class CreateRequiresForm(forms.ModelForm):
    class Meta:
        model = Requires
        fields = ['requires']

    def __init__(self, *args, **kwargs):
        # pass appointment in form parameters
        self.appointment = kwargs.pop('appointment', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        requires = super().save(commit=False)

        requires.appointment = self.appointment
        if commit:
            requires.save()

        return requires