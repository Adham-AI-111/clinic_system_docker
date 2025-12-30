from django.shortcuts import render, redirect, get_object_or_404
from .forms import ReceptionSignupForm
from common.permissions import doctor_required, staff_required

@doctor_required
def reception_signup(request):
    if request.method == 'POST':
        form = ReceptionSignupForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ReceptionSignupForm(request=request)
    context = {'form':form}
    return render(request, 'doctor/add_reception.html', context)
