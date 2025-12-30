from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import logging
from django.db.models import F, Q, OuterRef, Subquery, DateTimeField
from django.db import connection
from patient.models import Patient, Appointment
from common.permissions import staff_required
from common.auth_utils import guard_public_schema
from common.shared_forms import CreateAppointmentForm
from django_tenants.utils import get_public_schema_name

def home(request):
    '''
    The entry point for the system -- login URLs / public landing page
    '''
    # print("Current schema:", connection.schema_name)

    # Redirect authenticated users
    if request.user.is_authenticated and connection.schema_name != get_public_schema_name():
        if getattr(request.user, 'is_staff_member', False):
            return redirect('dashboard')
        else:
            return redirect('patient-profile', user_id=request.user.id)

    # Render public schema home
    if connection.schema_name == get_public_schema_name():
        # ! return the public shema url from the settings cause finite loop
        return render(request, "public/home.html")

    # Render tenant home/dashboard
    return render(request, "doctor/home.html")


@staff_required
def patients_dash(request):
    # Guard: Prevent accessing tenant-only views from public schema
    public_guard = guard_public_schema(request)
    if public_guard:
        return public_guard
    
    # I query every instance in patient model with its related data in user model, beacuse the depend steps need the user id
    patients = Patient.objects.select_related('user').all()

    q = request.GET.get('q')
    q_value = Q()
    if q:
        q_value = Q(user__username__icontains=q)| Q(id=q)
    patients = patients.filter(q_value)
    
    # Subquery: get the earliest future appointment per patient
    # TODO: make it in the service layer
    future_qs = Appointment.objects.filter(
        patient=OuterRef('pk'),         # match each patient
        date__gt=timezone.now()   # only future appointments
    ).order_by('created_at')            # earliest first

    # Annotate patients with next appointment ID and date
    patients = patients.annotate(
        next_appoint_id=Subquery(future_qs.values('id')[:1]),
        next_appoint_date=Subquery(future_qs.values('date')[:1], output_field=DateTimeField())
    )
    # print([a.next_appoint_date for a in patients ])
    # ? use -> patient.next_appoint_date  -> to display the date

    return render(request, 'doctor/patients.html', {'patients':patients})


@staff_required
def appointments_dash(request):
    '''
    all appointments for the current doctor are on the system
    '''
    # Guard: Prevent accessing tenant-only views from public schema
    public_guard = guard_public_schema(request)
    if public_guard:
        return public_guard
    
    # date filter - get these first
    first_date = request.GET.get('first_date')
    last_date = request.GET.get('last_date')
    filters = {}
    if first_date and last_date:
        filters['date__range'] = (first_date, last_date)
    elif first_date:
        filters['date__gte'] = first_date
    elif last_date:
        filters['date__lte'] = last_date
    
    # Query all appointments first, then fetch related data
    appointments = Appointment.objects.filter(**filters).select_related(
            'patient',
            'patient__user'
        ).order_by('-created_at')
    
    # Add annotated fields in Python to avoid filtering issues
    for appoint in appointments:
        appoint.patient_name = appoint.patient.user.username if appoint.patient and appoint.patient.user else ''
        appoint.patient_age = appoint.patient.age if appoint.patient else 0
        appoint.patient_ID = appoint.patient.id if appoint.patient else 0

    context = {'appointments':appointments}
    return render(request, 'doctor/appointments_history.html', context)


@staff_required
def update_appointment(request, appoint_id, user_id):
    '''
    Update an appointment from the appointment detail page
    Doctor can update: date, status, and is_prior fields
    Reuses add_appointment.html template for consistency
    '''
    appointment = get_object_or_404(Appointment, id=appoint_id)
    user = appointment.patient.user
    
    if request.method == 'POST':
        form = CreateAppointmentForm(request.POST, instance=appointment, patient=appointment.patient)
        if form.is_valid():
            appointment = form.save(commit=False)
            # Set cost using tenant (Doctor) fields when is_prior changes
            doctor_tenant = request.tenant
            if appointment.is_prior and getattr(doctor_tenant, 'default_prior_cost', None) is not None:
                appointment.cost = doctor_tenant.default_prior_cost
            elif getattr(doctor_tenant, 'default_cost', None) is not None:
                appointment.cost = doctor_tenant.default_cost
            appointment.save()
            messages.success(request, 'تم تحديث الموعد بنجاح')
            return redirect('appointment-details', appoint_id=appointment.id, user_id=user_id)
        else:
            context = {
                'form': form,
                'user': user,
            }
            return render(request, 'reception/add_appointment.html', context)
    else:
        form = CreateAppointmentForm(instance=appointment, patient=appointment.patient)
        context = {
            'form': form,
            'user': user,
        }
        return render(request, 'reception/add_appointment.html', context)


@staff_required
def delete_appointment(request, appoint_id, user_id):
    '''
    Delete an appointment from the appointment detail page
    Staff can delete an appointment
    '''
    appointment = get_object_or_404(Appointment, id=appoint_id)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'تم حذف الموعد بنجاح')
        return redirect('patient-profile', user_id=user_id)
    
    # GET request - show confirmation
    context = {
        'appointment': appointment,
        'user_id': user_id
    }
    return render(request, 'doctor/partials/delete_appointment_confirm.html', context)


#! is handing forms in appointmnet details will be better here or in patient app?
