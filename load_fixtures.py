import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maineblanc_project.settings')
django.setup()

from django.core.management import call_command

# Charger les fixtures
call_command('migrate')  # crée la base si besoin
call_command('loaddata', 'core/fixtures/core_fixture.json')
call_command('loaddata', 'reservations/fixtures/reservations_fixture.json')
call_command('loaddata', 'bookings/fixtures/bookings_fixture.json')
