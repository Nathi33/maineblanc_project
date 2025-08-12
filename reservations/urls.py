from django.urls import path
from .views import reservation_request_view

urlpatterns = [
    path('reservation/', reservation_request_view, name='reservation_request'),
]
