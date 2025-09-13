from django.shortcuts import render, redirect, reverse
from .forms import BookingFormClassic,BookingDetailsForm
from .models import Booking, Capacity, SupplementPrice
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from decimal import Decimal
from datetime import date
from django.utils import translation
from django.core.exceptions import ValidationError
import deepl
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
site_url = settings.SITE_URL


# --- Étape 1 : Formulaire réservation ---
def booking_form(request):
    # Récupère les données existantes dans la session pour pré-remplir
    initial_data = request.session.get('booking_data', {})
    booking_session_data = {}

    if request.method == 'POST':
        form = BookingFormClassic(request.POST)
        if form.is_valid():
            booking_data = form.cleaned_data
            booking_subtype = booking_data.get('booking_subtype')
            # booking_type = booking_data.get('booking_type')
            start_date = booking_data.get('start_date')
            end_date = booking_data.get('end_date')

            # Reconstituer un objet Booking pour validation
            temp_booking = Booking(
                booking_type=booking_subtype,
                start_date=start_date,
                end_date=end_date,
            )

            # Vérification de la disponibilité via full_clean()
            try:
                temp_booking.check_capacity()
            except ValidationError as e:
                form.add_error(None, e.messages[0])
                return render(request, 'bookings/booking_form.html', {'form': form})
            
            # Stockage temporaire dans la session
            for field, value in booking_data.items():
                if isinstance(value, Decimal):
                    booking_session_data[field] = float(value)
                elif isinstance(value, date):
                    booking_session_data[field] = value.isoformat()
                else:
                    booking_session_data[field] = value
            
            # Sauvegarde le type principal
            booking_session_data['booking_type'] = booking_subtype
            # Sauvegarde le sous-type exact choisi par l'utilisateur
            booking_session_data['booking_subtype'] = booking_subtype
            # Sauvegarde le choix de l'électricité
            booking_session_data['electricity'] = booking_data.get('electricity')
            # Marque la réservation comme non-ouvrier
            booking_session_data['is_worker'] = False
            
            # Enregistrer en session
            request.session['booking_data'] = booking_session_data

            return redirect('booking_summary')
    else:
        # Pré-remplissage correct avec le sous-type exact
        initial_dict = initial_data.copy()
        if initial_data:
            initial_dict['booking_type'] = initial_data.get('booking_subtype', initial_data.get('booking_type'))
        form = BookingFormClassic(initial=initial_dict)
        
    return render(request, 'bookings/booking_form.html', {'form': form})

# --- Étape 2 : Résumé réservation ---
def booking_summary(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('booking_form')
    
    # Reconstituer les dates
    booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
    booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

    # Reconstruire l'objet Booking
    model_fields = [f.name for f in Booking._meta.get_fields()]
    booking_data = {k: v for k, v in booking_data.items() if k in model_fields}
    booking = Booking(**booking_data)

    # Gérer l'affichage du choix électricité
    electricity_choice = booking_data.get('electricity', 'yes')
    booking.electricity = electricity_choice
    booking.electricity_display = "Avec électricité" if electricity_choice == 'yes' else "Sans électricité"

    # Sous-type exact choisi par l'utilisateur
    booking_subtype = booking_data.get('booking_subtype')
    subtype_display_map = {
        'tent': _("Tente"),
        'car_tent': _("Voiture Tente"),
        'caravan': _("Caravane"),
        'fourgon': _("Fourgon"),
        'van': _("Van"),
        'camping_car': _("Camping-car"),
    }
    booking.booking_subtype_display = subtype_display_map.get(
        booking_subtype,
        booking_subtype.replace('_', ' ').capitalize()
    )
    
    # Déterminer si c'est une tente ou un véhicule pour le template
    booking.is_tent = booking_subtype in ['tent', 'car_tent']
    booking.is_vehicle = booking_subtype in ['caravan', 'fourgon', 'van', 'camping_car']

    # Gérer le type principal pour le calcul du prix
    subtype_to_main = {
        'tent': 'tent',
        'car_tent': 'tent',
        'caravan': 'caravan',
        'fourgon': 'caravan',
        'van': 'caravan',
        'camping_car': 'camping_car',
    }
    booking.booking_type = subtype_to_main.get(booking_subtype, booking_subtype)

    # Calcul du prix total et de l'acompte
    supplement = SupplementPrice.objects.first()
    total_price = booking.calculate_total_price(supplement=supplement)
    deposit = booking.calculate_deposit()
    remaining_balance = round(total_price - deposit, 2)

    return render(request, 'bookings/booking_summary.html', {
        'booking': booking, 
        'total_price': total_price,
        'deposit': deposit,
        'remaining_balance': remaining_balance
    })

# --- Étape 3 : Coordonnées du client ---
def booking_details(request):
    # Récupérer ou créer booking_data
    booking_data = request.session.get('booking_data', {})

    if request.method == 'POST':
        form = BookingDetailsForm(request.POST)
        if form.is_valid():
            # Ajoute les infos client à la session
            booking_data.update(form.cleaned_data)
            request.session['booking_data'] = booking_data

            # Filtrer les champs du modèle Booking
            model_fields = [f.name for f in Booking._meta.get_fields()]
            booking_data = {k: v for k, v in booking_data.items() if k in model_fields}

            # Convertir les dates si elles sont en string
            if isinstance(booking_data.get('start_date'), str):
                booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
            if isinstance(booking_data.get('end_date'), str):
                booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

            # Reconstruire l'objet Booking
            booking = Booking(**booking_data)

            # Calcul de l'acompte
            deposit = booking.calculate_deposit()

            # --- Créer la session de paiement Stripe ---
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f"Acompte réservation camping ({booking.start_date} - {booking.end_date})",
                        },
                        'unit_amount': int(deposit * 100),  # Montant en centimes
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('booking_confirm')),
                cancel_url=request.build_absolute_uri(reverse('booking_details')),
                customer_email=booking_data.get('email'),
            )

            # Redirige l'utilisateur vers Stripe
            return redirect(checkout_session.url, code=303)

    else:
        form = BookingDetailsForm(initial=booking_data)

    return render(request, 'bookings/booking_details.html', {
        'form': form,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY

    })

# --- Étape 4 : Confirmation et enregistrement ---
def booking_confirm(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        messages.error(request, _("Aucune donnée de réservation trouvée. Veuillez recommencer le processus de réservation."))
        return redirect('booking_form')
    
    # Vérifie que les coordonnées sont présentes
    required_fields = ['first_name', 'last_name', 'address', 'postal_code', 'city', 'email', 'phone']
    if not all(field in booking_data for field in required_fields):
        messages.error(request, _("Les informations de contact sont incomplètes. Veuillez compléter vos coordonnées."))
        return redirect('booking_details')

    # Reconstitue les dates
    booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
    booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

    # Garde une copie des coordonnées client pour l'email
    client_address = booking_data.get('address')
    client_postal_code = booking_data.get('postal_code')
    client_city = booking_data.get('city')

    # Reconstruire l'objet Booking avec les champs du modèle
    model_fields = [f.name for f in Booking._meta.get_fields()]
    booking_data = {k: v for k, v in booking_data.items() if k in model_fields}
    booking = Booking(**booking_data)

    # Ajout des dimensions spécifiques selon le type
    booking.vehicle_length = booking_data.get('vehicle_length')
    booking.tent_length = booking_data.get('tent_length')
    booking.tent_width = booking_data.get('tent_width')
    booking.cable_length = booking_data.get('cable_length')

    # Gérer l'affichage du choix électricité
    electricity_choice = booking_data.get('electricity', 'yes')
    booking.electricity = electricity_choice
    booking.electricity_display = _("Avec électricité") if electricity_choice == 'yes' else _("Sans électricité")

    # Affichage exact du type d'hébergement
    subtype_display_map = {
        'tent': _("Tente"),
        'car_tent': _("Voiture Tente"),
        'caravan': _("Caravane"),
        'fourgon': _("Fourgon"),
        'van': _("Van"),
        'camping_car': _("Camping-car"),
    }
    booking.booking_subtype_display = subtype_display_map.get(booking.booking_subtype, booking.booking_subtype)

    # Déterminer si c'est une tente ou un véhicule pour le template
    booking.is_tent = booking.booking_subtype in ['tent', 'car_tent']
    booking.is_vehicle = booking.booking_subtype in ['caravan', 'fourgon', 'van', 'camping_car']

    # Calcul du prix total et de l'acompte
    supplement = SupplementPrice.objects.first()
    total_price = booking.calculate_total_price(supplement=supplement)
    deposit = booking.calculate_deposit()

    # Marquer l'acompte comme payé
    booking.deposit_paid = True

    # Sauvegarde de la réservation en base
    booking.save()

    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    # --- Infos supplémentaires pour l'email ---
    with translation.override('fr'):
        extra_info_1 = ""
        extra_info_2 = ""

        if booking.is_tent:
            extra_info_1 = _("Dimensions tente : {length} m x {width} m").format(
                length=booking.tent_length, width=booking.tent_width
            )
        elif booking.is_vehicle:
            extra_info_1 = _("Longueur véhicule : {length} m").format(
                length=booking.vehicle_length
            )
        if booking.electricity == 'yes':
            extra_info_2 = _("Longueur câble : {length} m").format(
                length=booking.cable_length
            )
    
        admin_subject = _("Nouvelle réservation de {booking.first_name} {booking.last_name}").format(booking=booking)
        admin_message_final = render_to_string('emails/admin_booking.html', {
            'booking': booking,
            'total_price': total_price,
            'deposit': deposit,
            'extra_info_1': extra_info_1,
            'extra_info_2': extra_info_2,
            'site_url': site_url,
            'address': client_address,
            'postal_code': client_postal_code,
            'city': client_city,
            'remaining_balance': round(total_price - deposit, 2)
        })

    email_admin = EmailMessage(
        subject=admin_subject,
        body=admin_message_final,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
    )
    email_admin.content_subtype = "html"
    email_admin.send(fail_silently=False)

    # --- Email client (dans la langue choisie) ---
    with translation.override(request.LANGUAGE_CODE):
        extra_info_1 = ""
        extra_info_2 = ""
        if booking.is_tent:
            extra_info_1 = _("Dimensions tente : {length} m x {width} m").format(
                length=booking.tent_length, width=booking.tent_width
            )
        elif booking.is_vehicle:
            extra_info_1 = _("Longueur véhicule : {length} m").format(
                length=booking.vehicle_length
            )
        if booking.electricity == 'yes':
            extra_info_2 = _("Longueur câble : {length} m").format(
                length=booking.cable_length
            )
            
        client_subject = _("Confirmation de votre réservation - Camping Le Maine Blanc")
        # Traduire automatiquement toutes les informations en français
        client_message = render_to_string('emails/client_booking.html', {
            'booking': booking,
            'total_price': total_price,
            'deposit': deposit,
            'extra_info_1': extra_info_1,
            'extra_info_2': extra_info_2,
            'site_url': site_url,
            'remaining_balance': round(total_price - deposit, 2)
        })
    
    email_client = EmailMessage(
        subject=client_subject,
        body=client_message,
        from_email=settings.EMAIL_FROM_CLIENT,
        to=[booking.email],
    )
    email_client.content_subtype = "html"
    email_client.send(fail_silently=False)

    # Nettoyage de la session
    if 'booking_data' in request.session:
        del request.session['booking_data']
    
    # Message de succès
    messages.success(
        request, 
        _("Merci ! Votre réservation a été confirmée. Un email de confirmation vous a été envoyé."))

    # Affichage de la page de confirmation
    return render(request, 'bookings/booking_confirm.html', {
        'booking': booking,
        'total_price': total_price,
        'deposit': deposit,
        'remaining_balance': round(total_price - deposit, 2)
    })

