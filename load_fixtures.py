import os
import django
import sys

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maineblanc_project.settings')
django.setup()

from django.core.management import call_command
from django.db import OperationalError

def load_fixture_safe(fixture_path):
    try:
        call_command('loaddata', fixture_path)
        print(f"✅ Fixture chargée : {fixture_path}")
    except OperationalError as e:
        print(f"⚠️ Ignoré problème de table pour {fixture_path} : {e}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {fixture_path} : {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔹 Appliquer toutes les migrations...")
    call_command('migrate', interactive=False)
    
    print("🔹 Chargement des fixtures...")
    load_fixture_safe('core/fixtures/core_fixture.json')
    load_fixture_safe('reservations/fixtures/reservations_fixture.json')
    load_fixture_safe('bookings/fixtures/bookings_fixture.json')
    
    print("🎉 Toutes les fixtures ont été chargées avec succès !")
