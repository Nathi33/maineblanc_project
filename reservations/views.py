from django.shortcuts import render
from .forms import ReservationRequestForm
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import override
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
import deepl


def reservation_request_view(request):
    if request.method == "POST":
        form = ReservationRequestForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # --- Traduction automatique du message libre du client ---
            message_client = cleaned_data.get('message', '')
            translated_message = "Aucun message"
            if message_client:
                try:
                    translator = deepl.Translator(settings.DEEPL_API_KEY)
                    result = translator.translate_text(message_client, target_lang="FR")
                    translated_message = result.text
                except Exception as e:
                    # Si l'API échoue, on garde le message original
                    translated_message = message_client + "\n\n(⚠️ Erreur de traduction automatique)"

            # --- Préparation des données pour le template ---
            booking_info = {
                'name': cleaned_data.get('name'),
                'first_name': cleaned_data.get('first_name'),
                'address': cleaned_data.get('address'),
                'postal_code': cleaned_data.get('postal_code'),
                'city': cleaned_data.get('city'),
                'phone': cleaned_data.get('phone'),
                'email': cleaned_data.get('email'),

                'start_date': cleaned_data.get('start_date'),
                'end_date': cleaned_data.get('end_date'),

                'accommodation_value': cleaned_data.get('accommodation_type'),
                'accommodation_label': dict(form.fields['accommodation_type'].choices).get(
                    cleaned_data.get('accommodation_type'), cleaned_data.get('accommodation_type')),

                'adults': cleaned_data.get('adults'),
                'children_over_8': cleaned_data.get('children_over_8'),
                'children_under_8': cleaned_data.get('children_under_8'),
                'pets': cleaned_data.get('pets'),
                'electricity': cleaned_data.get('electricity'),

                'tent_length': cleaned_data.get('tent_length'),
                'tent_width': cleaned_data.get('tent_width'),
                'vehicle_length': cleaned_data.get('vehicle_length'),
                'cable_length': cleaned_data.get('cable_length'),

                'translated_message': translated_message,
                'today': timezone.now().date(),
            }

            # --- Envoi de l'email à l'admin en français via template ---
            with override('fr'):
                subject = _("Nouvelle demande de réservation")
                message_html = render_to_string('reservations/email_admin.html', booking_info)
                
                email_admin = EmailMessage(
                    subject = subject,
                    body = message_html,
                    from_email = settings.DEFAULT_FROM_EMAIL,
                    to = [settings.ADMIN_EMAIL],
                )
                email_admin.content_subtype = "html"
                email_admin.send(fail_silently=False)

            # Message de confirmation pour le client 
            messages.success(
                request, 
                _("Votre demande de réservation a été envoyée avec succès. Nous reviendrons vers vous très rapidement.")
            )

            # Réinitialisation du formulaire
            form = ReservationRequestForm()

    else:
        form = ReservationRequestForm()
    
    return render(request, 'reservations/reservation_request.html', {'form': form})