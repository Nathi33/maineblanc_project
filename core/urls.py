from django.urls import path
from . import views
from django.conf.urls import handler404

urlpatterns = [
    path('', views.home_view, name='home'),
    path('a-propos/', views.about_view, name='about'),
    path('hebergements/', views.accommodations_view, name='accommodations'),
    path('services/', views.services_view, name='services'),
    path('infos-pratiques/', views.infos_view, name='infos'),
    path('activites/', views.activities_view, name='activities'),
    path('mentions-legales/', views.legal_view, name='legal'),
    path('politique-de-confidentialite/', views.privacy_view, name='privacy-policy'),
    path('notfound-test/', views.not_found_view, name='not_found'),
    path('robots.txt', views.robots_txt, name='robots_txt')
]

handler404 = views.not_found_view