from django.shortcuts import render, redirect, reverse
from .forms import BookingFormClassic,BookingDetailsForm
from .models import Booking, Capacity, SupplementPrice
from decimal import Decimal
from datetime import date
from django.utils.translation import gettext_lazy as _
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


# --- Étape 1 : Formulaire réservation ---
def booking_form(request):
    # Récupère les données existantes dans la session pour pré-remplir
    initial_data = request.session.get('booking_data')
    booking_session_data = {}

    if request.method == 'POST':
        form = BookingFormClassic(request.POST)
        if form.is_valid():
            booking_data = form.cleaned_data
            booking_subtype = booking_data.get('booking_subtype')
            booking_type = booking_data.get('booking_type')
            start_date = booking_data.get('start_date')
            end_date = booking_data.get('end_date')

            # Vérification de la disponibilité
            try:
                capacity = Capacity.objects.get(booking_type=booking_type)
            except Capacity.DoesNotExist:
                form.add_error('booking_type', "Aucune disponibilité trouvée.")
                return render(request, 'bookings/booking_form.html', {'form': form})

            overlapping = Booking.objects.filter(
                booking_type=booking_type,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).count()

            if overlapping >= capacity.max_places:
                form.add_error(None, "Désolé, il n'y a plus de disponibilité pour ce type de réservation aux dates choisies.")
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
        if initial_data:
            initial_dict = initial_data.copy()
            initial_dict['booking_type'] = initial_data.get('booking_subtype', initial_data.get('booking_type'))
            form = BookingFormClassic(initial=initial_dict)
        else:
            form = BookingFormClassic()

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
        return redirect('booking_form')
    
    # Vérifie que les coordonnées sont présentes
    required_fields = ['first_name', 'last_name', 'address', 'postal_code', 'city', 'email', 'phone']
    if not all(field in booking_data for field in required_fields):
        return redirect('booking_details')

    # Reconstitue les dates
    booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
    booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

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
    booking.electricity_display = "Avec électricité" if electricity_choice == 'yes' else "Sans électricité"

    # Sous-type exact choisi par l'utilisateur
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

    # Nettoyage de la session
    del request.session['booking_data']

    # Affichage de la page de confirmation
    return render(request, 'bookings/booking_confirm.html', {
        'booking': booking,
        'total_price': total_price,
        'deposit': deposit,
        'remaining_balance': round(total_price - deposit, 2)
    })

