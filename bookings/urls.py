from django.urls import path
from . import views


urlpatterns = [
    path('reservation/form/', views.booking_form, name='booking_form'),
    path('reservation/resume/', views.booking_summary, name='booking_summary'),
    path('reservation/coordonnees/', views.booking_details, name='booking_details'),
    path('reservation/confirmation/', views.booking_confirm, name='booking_confirm'),
]