from django.urls import path
from . import views, views_auth

urlpatterns = [
    path('patient-signup/', views_auth.signup_patient, name='patient-signup'),
    path('patient-login/', views_auth.patient_login, name='patient-login'),
    path('patient-logout/', views_auth.patient_logout, name='patient-logout'),
    path('patient-profile/<int:user_id>/', views.patient_profile, name='patient-profile'),
    path('appointment-details/<int:appoint_id>/<int:user_id>/', views.appointment_details, name='appointment-details'),
    path('add-diagnosis/<int:appoint_id>', views.create_diagnosis, name='add-diagnosis'),
    path('update-diagnosis/<int:diagnosis_id>', views.update_diagnosis, name='update-diagnosis'),
    path('view-diagnosis/<int:diagnosis_id>/', views.view_diagnosis, name='view-diagnosis'),
    path('delete-diagnosis/<int:diagnosis_id>/', views.delete_diagnosis, name='delete-diagnosis'),
    path('add-prescription/<int:appoint_id>', views.create_prescription, name='add-prescription'),
    path('update-prescription/<int:prescription_id>', views.update_prescription, name='update-prescription'),
    path('view-prescription/<int:prescription_id>/', views.view_prescription, name='view-prescription'),
    path('delete-prescription/<int:prescription_id>/', views.delete_prescription, name='delete-prescription'),
    path('add-requires/<int:appoint_id>', views.create_requires, name='add-requires'),
    path('update-requires/<int:requires_id>', views.update_requires, name='update-requires'),
    path('view-requires/<int:requires_id>/', views.view_requires, name='view-requires'),
    path('delete-requires/<int:requires_id>/', views.delete_requires, name='delete-requires'),
]
