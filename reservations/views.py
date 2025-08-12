from django.shortcuts import render, redirect
from .forms import ReservationRequestForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _


def reservation_request_view(request):
    if request.method == "POST":
        form = ReservationRequestForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            sujet = "Nouvelle demande de réservation"
            message = (
                f"Nouvelle demande de réservation :\n\n"
                f"Nom : {cleaned_data.get('name')} {cleaned_data.get('first_name')}\n"
                f"Adresse : {cleaned_data.get('address')} {cleaned_data.get('postal_code')} {cleaned_data.get('city')}\n"
                f"Téléphone : {cleaned_data.get('phone')}\n"
                f"Email : {cleaned_data.get('email')}\n"
                f"Date souhaitée : du {cleaned_data.get('start_date')} au {cleaned_data.get('end_date')}\n"
                f"Type d'hébergement : {cleaned_data.get('accommodation_type')}\n"
                f"Nombre d'occupants : {cleaned_data.get('adults')} adultes, {cleaned_data.get('children_over_8')} enfants +8 ans, {cleaned_data.get('children_under_8')} enfants -8 ans, {cleaned_data.get('pets')} animaux de compagnie\n"
                f"Electricité : {cleaned_data.get('electricity')}\n"
                f"Message : {cleaned_data.get('message')}\n"
            )
            send_mail(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            messages.success(request, _("Votre demande de réservation a bien été envoyée, nous reviendrons vers vous très rapidement."))

            form = ReservationRequestForm()

    else:
        form = ReservationRequestForm()

    return render(request, 'reservations/reservation_request.html', {'form': form})
