from functools import cache
from django.shortcuts import render, redirect, get_object_or_404
from common.permissions import staff_required
from common.auth_utils import guard_public_schema
from common.shared_forms import CreateAppointmentForm
from doctor.models import User, Doctor
from patient.models import Patient, Appointment
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery
from django.db import connection
from django.core.cache import cache


@staff_required
def dashboard(request):
    # Guard: Prevent accessing tenant-only views from public schema
    public_guard = guard_public_schema(request)
    if public_guard:
        return public_guard
    
    today = timezone.now().date()
    today_appoints = Appointment.objects.select_related(
        'patient',
        'patient__user'
    ).filter(date=today).order_by('created_at') # oldest first

    # !-------------------------
    # Get previous appointment for each appointment by user
    #TODO : add it to a service layer
    previous_qs = Appointment.objects.filter(
        patient=OuterRef('patient'),
        created_at__lt=OuterRef('created_at')
    ).order_by('-created_at')

    today_appoints = today_appoints.annotate(
        previous_appoint_id=Subquery(previous_qs.values('id')[:1])
    )
    # !-------------------------

    total_today_revenue = today_appoints.aggregate(total_cost=Sum('cost'))
    delayed_appoints = today_appoints.filter(status='Pending')       
    complated_appoints = today_appoints.filter(status='Completed')
    prior_appoints = today_appoints.filter(is_prior=True)

    # because i using the dynamin form the colors need a dict to deter. the class
    status_classes = {
    'Completed': 'success',
    'Pending': 'warning',
    'Canceled': 'muted',
    }
    context = {
        'today':today,
        'today_appoints':today_appoints,
        'total_today_revenue':total_today_revenue,
        'delayed_appoints':delayed_appoints,
        'complated_appoints':complated_appoints,
        'prior_appoints':prior_appoints,
        'status_classes':status_classes,
    }
    return render(request, 'reception/dashboard.html', context)


@staff_required
def create_appointment(request, pk):
    '''
    - will done from user profile
    - pk is the user instance id passed from patient profile
    '''
    user = get_object_or_404(User, id=pk)
    # for link between appointment and the patient in the form
    patient = get_object_or_404(Patient, user=user)
    # print(patient.id)

    # Get the next URL from GET or POST request
    next_url = request.GET.get('next') or request.POST.get('next_url')

    if request.method == 'POST':
        form = CreateAppointmentForm(request.POST, patient=patient)
        if form.is_valid():
            appointment = form.save(commit=False)
            # Set cost using tenant (Doctor) fields
            doctor_tenant = request.tenant
            if appointment.is_prior and getattr(doctor_tenant, 'default_prior_cost', None) is not None:
                appointment.cost = doctor_tenant.default_prior_cost
            elif getattr(doctor_tenant, 'default_cost', None) is not None:
                appointment.cost = doctor_tenant.default_cost
            appointment.save()
            
            messages.success(request, 'appointment added successfully')
            # Redirect to next_url if provided, otherwise dashboard
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            print('error found')
    else:
        form = CreateAppointmentForm(patient=patient)
    context = {'form': form, 'user': user, 'next_url': next_url}
    return render(request, 'reception/add_appointment.html', context)

def update_appoint_status(request, pk):
    appoint = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Appointment.APPOINT_STATUS):
            appoint.status = new_status
            appoint.save(update_fields=["status"])
    
    context = {'appoint':appoint}
    return render(request, 'reception/partials/appoint_card.html', context)
