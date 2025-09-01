from django.urls import path
from . import views


urlpatterns = [
    path('new/', views.booking_form, name='booking_form'),
    path('success/', views.booking_success, name='booking_success'),
]