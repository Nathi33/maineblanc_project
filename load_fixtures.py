import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maineblanc_project.settings')
django.setup()

from django.core.management import call_command
from django.db import OperationalError

# Liste des fixtures à charger avec le chemin relatif depuis le projet
fixtures = [
    'core/fixtures/core_fixture.json',
    'reservations/fixtures/reservations_fixture.json',
    'bookings/fixtures/bookings_fixture.json',
]

def load_fixture(fixture_path):
    try:
        # Forcer l'encodage UTF-8 pour éviter les erreurs de caractère
        with open(fixture_path, encoding='utf-8') as f:
            data = json.load(f)
        # Charger la fixture
        call_command('loaddata', fixture_path)
        print(f"✅ Fixture chargée : {fixture_path}")
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé : {fixture_path}")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur d'encodage UTF-8 dans {fixture_path} : {e}")
    except OperationalError as e:
        # Ignorer les erreurs liées à des tables manquantes (par ex. les tables _translation)
        print(f"⚠️ Ignoré problème de table pour {fixture_path} : {e}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {fixture_path} : {e}")

if __name__ == "__main__":
    print("🔹 Migration de la base de données...")
    call_command('migrate')  # crée les tables si nécessaire

    print("🔹 Chargement des fixtures...")
    for fixture in fixtures:
        load_fixture(fixture)

    print("✅ Chargement des fixtures terminé !")
