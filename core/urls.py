from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_view, name='home'),
    path('a-propos/', views.about_view, name='about'),
    path('hebergements/', views.accommodations_view, name='accommodations'),
    path('services/', views.services_view, name='services'),
    path('infos-pratiques/', views.infos_view, name='infos'),
    path('activites/', views.activities_view, name='activities'),
    path('tarifs/', views.pricing_view, name='pricing'),
    path('reserver/', views.bookings_view, name='bookings'),
    path('mentions-legales/', views.legal_view, name='legal'),
    path('politique-de-confidentialite/', views.privacy_view, name='privacy-policy'),
]