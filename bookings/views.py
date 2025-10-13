from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import BookingFormClassic,BookingDetailsForm
from .models import Booking, SupplementPrice
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date
from django.utils import translation
from django.core.exceptions import ValidationError
import stripe, socket, traceback

# Stripe configuration
stripe.api_key = settings.STRIPE_SECRET_KEY
site_url = settings.SITE_URL


# -----------------------------
# STEP 1: Reservation form (Booking type and dates)
# -----------------------------
def booking_form(request):
    """
    Display and process the initial booking form where the user selects:
    - Booking subtype (tent, caravan, etc.)
    - Start and end dates
    - Initial booking preferences (electricity, number of people...)

    Security:
    - Use Django forms for input validation.
    - Convert decimals and dates to safe formats before saving in session.
    - Validate capacity with Booking.check_capacity to prevent overbooking.
    """
    initial_data = request.session.get('booking_data', {})
    booking_session_data = {}

    if request.method == 'POST':
        form = BookingFormClassic(request.POST)
        if form.is_valid():
            booking_data = form.cleaned_data
            booking_subtype = booking_data.get('booking_subtype')
            start_date = booking_data.get('start_date')
            end_date = booking_data.get('end_date')

            # Temporary booking to check capacity
            if not start_date or not end_date:
                return render(request, 'bookings/booking_form.html', {'form': form})
            
            temp_booking = Booking(
                booking_type=booking_subtype,
                start_date=start_date,
                end_date=end_date,
            )

            # Validate availability (capacity)
            try:
                temp_booking.check_capacity()
            except ValidationError as e:
                form.add_error(None, e.messages[0])
                return render(request, 'bookings/booking_form.html', {'form': form})
            
            # Safely store data in session
            for field, value in booking_data.items():
                if isinstance(value, Decimal):
                    booking_session_data[field] = float(value)
                elif isinstance(value, date):
                    booking_session_data[field] = value.isoformat()
                else:
                    booking_session_data[field] = value
            
            booking_session_data['booking_type'] = booking_subtype
            booking_session_data['booking_subtype'] = booking_subtype
            booking_session_data['electricity'] = booking_data.get('electricity')
            booking_session_data['is_worker'] = False
            
            request.session['booking_data'] = booking_session_data
            return redirect('booking_summary')
    else:
        initial_dict = initial_data.copy()
        if initial_data:
            initial_dict['booking_type'] = initial_data.get('booking_subtype', initial_data.get('booking_type'))
        form = BookingFormClassic(initial=initial_dict)
        
    return render(request, 'bookings/booking_form.html', {'form': form})

# -----------------------------
# STEP 2: Summary before validation
# -----------------------------
def booking_summary(request):
    """
    Display a booking summary before payment.
    Validates session data and shows:
    - Total price
    - Deposit amount
    - Remaining balance
    """
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('booking_form')
    
    # Convert stored ISO dates back to date objects
    start_date = date.fromisoformat(booking_data['start_date'])
    end_date = date.fromisoformat(booking_data['end_date'])

    # Keep only model fields to avoid injection
    model_fields = [f.name for f in Booking._meta.get_fields()]
    booking_data_for_model = {k: v for k, v in booking_data.items() if k in model_fields}
    booking_data_for_model['start_date'] = start_date
    booking_data_for_model['end_date'] = end_date
    booking = Booking(**booking_data_for_model)

    # Electricity display
    electricity_choice = booking_data.get('electricity', 'yes')
    booking.electricity = electricity_choice
    booking.electricity_display = "Avec électricité" if electricity_choice == 'yes' else "Sans électricité"

    # Display for subtype
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
    
    # Category helpers
    booking.is_tent = booking_subtype in ['tent', 'car_tent']
    booking.is_vehicle = booking_subtype in ['caravan', 'fourgon', 'van', 'camping_car']

    # Map subtypes to main type for pricing
    subtype_to_main = {
        'tent': 'tent',
        'car_tent': 'tent',
        'caravan': 'caravan',
        'fourgon': 'caravan',
        'van': 'caravan',
        'camping_car': 'camping_car',
    }
    booking.booking_type = subtype_to_main.get(booking_subtype, booking_subtype)

    # Price calculations
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

# -----------------------------
# STEP 3: Customer details and Stripe session
# -----------------------------
def booking_details(request):
    """
    Collect customer's personal details.
    Once valid, create a Stripe Checkout session for deposit payment.


    Security:
    - Never trust session directly, always validate with Django form.
    - Stripe key is read from Django settings.
    """
    booking_data = request.session.get('booking_data', {})

    if request.method == 'POST':
        form = BookingDetailsForm(request.POST)
        if form.is_valid():
            booking_data.update(form.cleaned_data)
            request.session['booking_data'] = booking_data

            # Filter and clean model fields
            model_fields = [f.name for f in Booking._meta.get_fields()]
            booking_data = {k: v for k, v in booking_data.items() if k in model_fields}

            # Convert dates safely
            if isinstance(booking_data.get('start_date'), str):
                booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
            if isinstance(booking_data.get('end_date'), str):
                booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

            booking = Booking(**booking_data)
            deposit = booking.calculate_deposit()

            # Create Stripe Checkout session
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': f"Acompte réservation camping ({booking.start_date} - {booking.end_date})",
                            },
                            'unit_amount': int(deposit * 100),  # Amount in cents
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=f"{settings.SITE_URL}{reverse('booking_confirm')}",
                    cancel_url=f"{settings.SITE_URL}{reverse('booking_details')}",
                    customer_email=booking_data.get('email'),
                )
            
                return redirect(checkout_session.url, code=303)
            except stripe.error.StripeError as e:
                print("⚠️ Stripe Error:", e)
                traceback.print_exc()
                return render(request, 'bookings/booking_details.html', {
                    'form': form,
                    'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
                    'error_message': _("Impossible de traiter le paiement pour le moment. Veuillez réessayer.")
                })
    else:
        form = BookingDetailsForm(initial=booking_data)

    return render(request, 'bookings/booking_details.html', {
        'form': form,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY

    })

# -----------------------------
# STEP 4: Confirmation and email sending
# -----------------------------
def booking_confirm(request):
    """
    Final step:
    - Verify data integrity
    - Save booking in DB
    - Send confirmation emails (admin + customer)
    - Clear session


    Security:
    - Validate required fields before saving.
    - Remove all booking data from session after confirmation.
    """
    booking_data = request.session.get('booking_data')

    if not booking_data:
        messages.error(request, _("Aucune donnée de réservation trouvée. Veuillez recommencer le processus de réservation."))
        return redirect('booking_form')
    
    required_fields = ['first_name', 'last_name', 'address', 'postal_code', 'city', 'email', 'phone']
    if not all(field in booking_data for field in required_fields):
        messages.error(request, _("Les informations de contact sont incomplètes. Veuillez compléter vos coordonnées."))
        return redirect('booking_details')

    # Convert dates
    booking_data['start_date'] = date.fromisoformat(booking_data['start_date'])
    booking_data['end_date'] = date.fromisoformat(booking_data['end_date'])

    # Save client address details for email
    client_address = booking_data.get('address')
    client_postal_code = booking_data.get('postal_code')
    client_city = booking_data.get('city')

    # Rebuild the Booking object with model fields
    model_fields = [f.name for f in Booking._meta.get_fields()]
    booking_data = {k: v for k, v in booking_data.items() if k in model_fields}
    booking = Booking(**booking_data)

    # Additional fields
    booking.vehicle_length = booking_data.get('vehicle_length')
    booking.tent_length = booking_data.get('tent_length')
    booking.tent_width = booking_data.get('tent_width')
    booking.cable_length = booking_data.get('cable_length')

    # Electricity display
    electricity_choice = booking_data.get('electricity', 'yes')
    booking.electricity = electricity_choice
    booking.electricity_display = _("Avec électricité") if electricity_choice == 'yes' else _("Sans électricité")

    subtype_display_map = {
        'tent': _("Tente"),
        'car_tent': _("Voiture Tente"),
        'caravan': _("Caravane"),
        'fourgon': _("Fourgon"),
        'van': _("Van"),
        'camping_car': _("Camping-car"),
    }
    booking.booking_subtype_display = subtype_display_map.get(booking.booking_subtype, booking.booking_subtype)

    booking.is_tent = booking.booking_subtype in ['tent', 'car_tent']
    booking.is_vehicle = booking.booking_subtype in ['caravan', 'fourgon', 'van', 'camping_car']

    supplement = SupplementPrice.objects.first()
    total_price = booking.calculate_total_price(supplement=supplement)
    deposit = booking.calculate_deposit()
    
    # Mark deposit as paid and save
    booking.deposit_paid = True
    booking.save()

    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

    # Render
    hostname = socket.gethostname()
    is_render = "render" in hostname or "onrender" in site_url

    # Email to admin
    try:
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

            if is_render:
                print("📧 [SIMULATION ADMIN EMAIL] →", settings.ADMIN_EMAIL)
                print(admin_message_final)
            else:
                email_admin = EmailMessage(
                    subject=admin_subject,
                    body=admin_message_final,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.ADMIN_EMAIL],
                )
                email_admin.content_subtype = "html"
                email_admin.send(fail_silently=False)

        # Email to client in selected language
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

            client_message = render_to_string('emails/client_booking.html', {
                'booking': booking,
                'total_price': total_price,
                'deposit': deposit,
                'extra_info_1': extra_info_1,
                'extra_info_2': extra_info_2,
                'site_url': site_url,
                'remaining_balance': round(total_price - deposit, 2)
            })

            if is_render:
                print("📧 [SIMULATION CLIENT EMAIL] →", booking.email)
                print(client_message)
            else:
                email_client = EmailMessage(
                    subject=client_subject,
                    body=client_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[booking.email],
                )
                email_client.content_subtype = "html"
                email_client.send(fail_silently=False)
    
    except Exception as e:
        print("⚠️ Erreur lors de l'envoi des emails :", e)
        messages.warning(request, _("Votre réservation est enregistrée, mais une erreur est survenue lors de l'envoi des emails. Veuillez contacter l'administrateur."))

    # Clean session
    if 'booking_data' in request.session:
        del request.session['booking_data']
    
    messages.success(
        request, 
        _("Merci ! Votre réservation a été confirmée. Un email de confirmation vous a été envoyé." if not is_render else
          "Merci ! Votre réservation a été confirmée. (Simulation d'envoi d'email sur Render.)")
    )

    return render(request, 'bookings/booking_confirm.html', {
        'booking': booking,
        'total_price': total_price,
        'deposit': deposit,
        'remaining_balance': round(total_price - deposit, 2)
    })

