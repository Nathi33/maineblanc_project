from django.shortcuts import render, redirect
from .forms import ReservationRequestForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import override
import deepl


def reservation_request_view(request):
    if request.method == "POST":
        form = ReservationRequestForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # --- Forcer la langue française pour l'email ---
            with override('fr'):

                # --- Préparation des données de base pour l'email ---
                name = cleaned_data.get('name')
                first_name = cleaned_data.get('first_name')
                address = cleaned_data.get('address')
                postal_code = cleaned_data.get('postal_code')
                city = cleaned_data.get('city')
                phone = cleaned_data.get('phone')
                email = cleaned_data.get('email')

                start_date = cleaned_data.get('start_date').strftime('%d/%m/%Y') if cleaned_data.get('start_date') else None
                end_date = cleaned_data.get('end_date').strftime('%d/%m/%Y') if cleaned_data.get('end_date') else None

                accommodation_value = cleaned_data.get('accommodation_type')
                accommodation_label = dict(form.fields['accommodation_type'].choices).get(accommodation_value, accommodation_value)

                adults = cleaned_data.get('adults')
                children_over_8 = cleaned_data.get('children_over_8')
                children_under_8 = cleaned_data.get('children_under_8')
                pets = cleaned_data.get('pets')
                electricity = cleaned_data.get('electricity')
                message_client = cleaned_data.get('message')

                tent_length = cleaned_data.get('tent_length')
                tent_width = cleaned_data.get('tent_width')
                vehicle_length = cleaned_data.get('vehicle_length')
                cable_length = cleaned_data.get('cable_length')

                # --- Traduction du message client si nécessaire ---
                translated_message  =  "Aucun message"
                if message_client:
                    try:
                        translator = deepl.Translator(settings.DEEPL_API_KEY)
                        result = translator.translate_text(message_client, target_lang="FR")
                        translated_message = result.text
                    except Exception as e:
                        # Si l'API échoue, on garde le message original
                        translated_message = message_client + "\n\n(⚠️ Erreur de traduction automatique)"

                # --- Construction du message conditionnel ---
                extra_info_1 = ""

                # Si tente ou voiture tente, afficher longueur et largeur de la tente
                if accommodation_value in ['tent', 'car_tent']:
                    extra_info_1 += (
                        f"\nDimensions de la tente :\n"
                        f"  - Longueur : {tent_length} m\n"
                        f"  - Largeur : {tent_width} m\n"
                    )
                # Si caravane, fourgon, van ou camping-car, afficher longueur du véhicule
                if accommodation_value in ['caravan', 'fourgon', 'van', 'camping_car']:
                    extra_info_1 += f"\nLongueur : {vehicle_length} m\n"

                extra_info_2 = ""
                # Si électricité, afficher longueur du câble
                if electricity == 'yes':
                    extra_info_2 += f"\nLongueur du câble électrique : {cable_length} m\n"

                # --- Message final ---
                email_message = (
                    "Nouvelle demande de réservation\n"
                    "===============================\n\n"
                    f"👤 **Informations du client**\n"
                    f"Nom : {name} {first_name}\n"
                    f"Adresse : {address}, {postal_code} {city}\n"
                    f"Téléphone : {phone}\n"
                    f"Email : {email}\n\n"

                    f"📅 **Dates souhaitées**\n"
                    f"Du {start_date} au {end_date}\n\n"

                    f"🏕 **Type d'hébergement**\n"
                    f"{accommodation_label}"
                    f"{extra_info_1}\n"

                    f"👥 **Occupants**\n"
                    f"- Adultes : {adults}\n"
                    f"- Enfants (+8 ans) : {children_over_8}\n"
                    f"- Enfants (-8 ans) : {children_under_8}\n"
                    f"- Animaux : {pets}\n\n"

                    f"🔌 **Électricité**\n" 
                    f"{'Avec électricité' if electricity == 'yes' else 'Sans électricité'}"
                    f"{extra_info_2}\n"

                    f"💬 **Message du client**\n"
                    f"{translated_message}\n"
                )

                # --- Envoi de l'email ---
                send_mail(
                    "Nouvelle demande de réservation",
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )

            # Message de confirmation pour le client
            messages.success(
                request,
                _("Votre demande de réservation a bien été envoyée, nous reviendrons vers vous très rapidement.")
            )

            # Réinitialisation du formulaire après envoi
            form = ReservationRequestForm()

    else:
        form = ReservationRequestForm()

    return render(request, 'reservations/reservation_request.html', {'form': form})
