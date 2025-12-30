import logging

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from common.permissions import doctor_required, user_owns_profile
from doctor.models import User

from .forms import (
    CreateDiagnosisForm,
    CreatePrescriptionForm,
    CreateRequiresForm,
)
from .models import Appointment, Diagnosis, Patient, Prescription, Requires
 
logger = logging.getLogger(__name__)

@user_owns_profile
def patient_profile(request, user_id):
    '''
    the single user appointments
    get by user_id the patient appointments
    '''
    
    user = User.objects.get(id=user_id) # get the patient instance in user model by user_id
    patient = Patient.objects.get(user=user) # get the patient instance itself in patient model
    appointments = Appointment.objects.filter(patient=patient)
    
    # i passed the user_id itself to use it in create appointment url
    context = {'user_id':user_id, 'patient':patient, 'appointments':appointments} # use patient to set his identifier data in profile, and appointment to redirect to appointment details
    return render(request, 'patient/patient_profile.html', context)

@user_owns_profile
def appointment_details(request, appoint_id, user_id):
    user = get_object_or_404(User, id=user_id)
    appointment = get_object_or_404(Appointment, id=appoint_id)
    
    # prevent user from request onther user appointment by pass user id manaually in the url
    # http://localhost:8000/patient/appointment-details/2/11/  ->this is the true path
    # http://localhost:8000/patient/appointment-details/2/7/  -> this is a vain path  (11 exchange to 7)
    #? the result is -> data that depends on user id will change but the  data that depends on appoint_id will not change
    if appointment.patient.user.id != user_id:
        return HttpResponseForbidden("Invalid URL parameters.")

    # ------ Get existing diagnosis for this appointment --------
    try:
        diagnosis = Diagnosis.objects.get(appointment=appointment)
        # or if there can be multiple: diagnosis = Diagnosis.objects.filter(appointment=appointment).first()
    except Diagnosis.DoesNotExist:
        diagnosis = None

    # ? handle prescription and requirements exits __instaed using try/except
    prescription = appointment.prescription if hasattr(appointment, 'prescription') else None
    
    # Get existing requires for this appointment
    try:
        requires = Requires.objects.get(appointment=appointment)
    except Requires.DoesNotExist:
        requires = None

    context = {
        'user':user,
        'appointment':appointment,
        'diagnosis': diagnosis, 
        'prescription':prescription,
        'requires': requires
        }
    return render(request, 'patient/appointment_details.html', context)



# !================ the dynamic forms logic in appointment details ==================
# ?the separate view func. for each one to avoid reload the page for cancel button
@doctor_required
def create_diagnosis(request, appoint_id):
    appoint = Appointment.objects.get(id=appoint_id)
    
    # debug the url 
    try:
        url = reverse('add-diagnosis', args=[appoint.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreateDiagnosisForm(request.POST, appointment=appoint)
        
        if form.is_valid():
            new_diagnosis = form.save()
            return render(request, 'patient/partials/diagnosis_view.html', {'diagnosis': new_diagnosis})
        else:
            # Return form with errors so user can see what's wrong
            context = {'form': form, 'appointment': appoint, 'model_name':'diagnosis'}
            return render(request, 'patient/partials/diagnosis_form.html', context)
    else:
        form = CreateDiagnosisForm(appointment=appoint)
    
    context = {
        'form': form,
        'appointment': appoint,
        'url_path':url,
        'model_name':'diagnosis',
        }
    return render(request, 'patient/partials/diagnosis_form.html', context)


@doctor_required
def update_diagnosis(request, diagnosis_id):
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)

    try:
        url = reverse('update-diagnosis', args=[diagnosis.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreateDiagnosisForm(request.POST, instance=diagnosis, appointment=diagnosis.appointment)
        if form.is_valid():
            updated_diagnosis = form.save()
            return render(request, 'patient/partials/diagnosis_view.html', {'diagnosis':updated_diagnosis})
        else:
            # Return form with errors
            context = {'form': form, 'url_path': url, 'model_name': 'diagnosis'}
            return render(request, 'patient/partials/diagnosis_form.html', context)
    else:
        form = CreateDiagnosisForm(instance=diagnosis, appointment=diagnosis.appointment)
    context = {
        'form':form,
        'url_path':url,
        'model_name':'diagnosis',
        }
    return render(request, 'patient/partials/diagnosis_form.html', context)


@doctor_required
def view_diagnosis(request, diagnosis_id):
    """View-only endpoint to return diagnosis view (for cancel button)"""
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    return render(request, 'patient/partials/diagnosis_view.html', {'diagnosis': diagnosis})


@doctor_required
def delete_diagnosis(request, diagnosis_id):
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    appointment = diagnosis.appointment

    # Delete the diagnosis
    diagnosis.delete()

    # Return empty card + show add button -> recycling
    return render(request, 'patient/partials/diagnosis_delete.html', {'appointment': appointment})


@doctor_required
def create_prescription(request, appoint_id):
    appoint = get_object_or_404(Appointment, id=appoint_id)
    if appoint == None:
        logger.info(f'cannot get the appointment {appoint_id} for saving the prescription')

    try:
        url = reverse('add-prescription', args=[appoint.id])
    except Exception as e:
        url = None
    
    if request.method == 'POST':
        form = CreatePrescriptionForm(request.POST, appointment=appoint)
        if form.is_valid():
            new_prescription = form.save()
            print('saved prescription')
            logger.info(f"successfully saving prescription {new_prescription.id}")
            return render(request, 'patient/partials/prescription_view.html', {'prescription': new_prescription})
            
        else:
            # Return form with errors so user can see what's wrong
            context = {'form': form, 'appointment': appoint}
            return render(request, 'patient/partials/prescription_form.html', context)
    else:
        form = CreatePrescriptionForm(appointment=appoint)

    context={
        'model_name':'prescription',
        'form':form,
        # 'prescription':new_prescription,
        'url_path':url,
    }
    return render(request, 'patient/partials/prescription_form.html', context)


@doctor_required
def update_prescription(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)

    try:
        url = reverse('update-prescription', args=[prescription.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreatePrescriptionForm(request.POST, instance=prescription, appointment=prescription.appointment)
        if form.is_valid():
            updated_prescription = form.save()
            return render(request, 'patient/partials/prescription_view.html', {'prescription':updated_prescription})
        else:
            # Return form with errors
            context = {'form': form, 'url_path': url, 'model_name': 'prescription'}
            return render(request, 'patient/partials/prescription_form.html', context)
    else:
        form = CreatePrescriptionForm(instance=prescription, appointment=prescription.appointment)
    context = {
        'form':form,
        'url_path':url,
        'model_name':'prescription',
        }
    return render(request, 'patient/partials/prescription_form.html', context)

    
@doctor_required
def view_prescription(request, prescription_id):
    """View-only endpoint to return prescription view (for cancel button)"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    return render(request, 'patient/partials/prescription_view.html', {'prescription': prescription})


@doctor_required
def delete_prescription(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)
    appointment = prescription.appointment

    # Delete the prescription
    prescription.delete()

    # Return empty card + show add button -> recycling
    return render(request, 'patient/partials/prescription_delete.html', {'appointment': appointment})


@doctor_required
def create_requires(request, appoint_id):
    appoint = get_object_or_404(Appointment, id=appoint_id)
    
    try:
        url = reverse('add-requires', args=[appoint.id])
    except Exception as e:
        url = None
    
    if request.method == 'POST':
        form = CreateRequiresForm(request.POST, appointment=appoint)
        if form.is_valid():
            new_requires = form.save()
            return render(request, 'patient/partials/requires_view.html', {'requires': new_requires})
        else:
            # Return form with errors so user can see what's wrong
            context = {'form': form, 'appointment': appoint, 'model_name': 'requires'}
            return render(request, 'patient/partials/requires_form.html', context)
    else:
        form = CreateRequiresForm(appointment=appoint)

    context = {
        'model_name': 'requires',
        'form': form,
        'url_path': url,
    }
    return render(request, 'patient/partials/requires_form.html', context)


@doctor_required
def update_requires(request, requires_id):
    requires = get_object_or_404(Requires, id=requires_id)

    try:
        url = reverse('update-requires', args=[requires.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreateRequiresForm(request.POST, instance=requires, appointment=requires.appointment)
        if form.is_valid():
            updated_appointment = form.save(commit=False)
            # Set cost using tenant (Doctor) fields
            doctor_tenant = request.tenant
            if updated_appointment.is_prior and getattr(doctor_tenant, 'default_prior_cost', None) is not None:
                updated_appointment.cost = doctor_tenant.default_prior_cost
            elif getattr(doctor_tenant, 'default_cost', None) is not None:
                updated_appointment.cost = doctor_tenant.default_cost
            updated_appointment.save()
            messages.success(request, 'appointment updated successfully')

            return render(request, 'patient/partials/requires_view.html', {'requires': updated_appointment})
        else:
            # Return form with errors
            context = {'form': form, 'url_path': url, 'model_name': 'requires'}
            return render(request, 'patient/partials/requires_form.html', context)
    else:
        form = CreateRequiresForm(instance=requires, appointment=requires.appointment)
    context = {
        'form': form,
        'url_path': url,
        'model_name': 'requires',
    }
    return render(request, 'patient/partials/requires_form.html', context)

    
@doctor_required
def view_requires(request, requires_id):
    """View-only endpoint to return requires view (for cancel button)"""
    requires = get_object_or_404(Requires, id=requires_id)
    return render(request, 'patient/partials/requires_view.html', {'requires': requires})


@doctor_required
def delete_requires(request, requires_id):
    requires = get_object_or_404(Requires, id=requires_id)
    appointment = requires.appointment

    # Delete the requires
    requires.delete()

    # Return empty card + show add button -> recycling
    return render(request, 'patient/partials/requires_delete.html', {'appointment': appointment})
# !===================================================================