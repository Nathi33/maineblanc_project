#!/bin/bash
# Active l'environnement virtuel
source /home/username/venv/bin/activate

# Se placer dans le dossier du projet
cd /home/username/camping_site/maineblanc_project

# Lancer la commande Django
python manage.py clean_old_bookings

# Désactiver l'environnement virtuel
deactivate
