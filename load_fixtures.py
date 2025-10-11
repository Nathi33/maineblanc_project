from django.core.management import call_command
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maineblanc_project.settings')
django.setup()

# 1️⃣ Appliquer toutes les migrations
call_command('migrate', interactive=False)

# 2️⃣ Charger les fixtures
call_command('loaddata', 'core/fixtures/core_fixture.json')
call_command('loaddata', 'reservations/fixtures/reservations_fixture.json')
call_command('loaddata', 'bookings/fixtures/bookings_fixture.json')
