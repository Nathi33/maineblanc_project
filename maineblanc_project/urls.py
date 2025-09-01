from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from users.views import register

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('reservations/', include('reservations.urls')),
    path('bookings/', include('bookings.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', register, name='register'),
)

