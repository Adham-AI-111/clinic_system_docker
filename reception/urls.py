from django.urls import path
from . import views, views_auth

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reception-signup/', views_auth.reception_signup, name='reception-signup'),
    path('create-appointment/<int:pk>/', views.create_appointment, name='create-appointment'),
    path('update-status/<int:pk>/', views.update_appoint_status, name='update-status'),
]
