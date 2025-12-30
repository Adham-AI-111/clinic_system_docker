from django.urls import path
from . import views, views_auth

urlpatterns = [
    path('', views.home, name='home'),
    path('staff-login/', views_auth.staff_login, name='staff-login'),
    path('staff-logout/', views_auth.staff_logout, name='staff-logout'),
    path('patients-dash/', views.patients_dash, name='patients-dash'),
    path('appointments-dash/', views.appointments_dash, name='appointments-dash'),
    path('update-appointment/<int:appoint_id>/<int:user_id>/', views.update_appointment, name='update-appointment'),
    path('delete-appointment/<int:appoint_id>/<int:user_id>/', views.delete_appointment, name='delete-appointment'),
]
