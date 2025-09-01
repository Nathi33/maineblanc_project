from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import BookingForm


def booking_form(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                # Stocke les données du formulaire dans la session
                request.session['booking_data'] = request.POST
                # Redirige vers login
                return redirect(f"{reverse('login')}?next={request.path}")
            # Si l'utilisateur est connecté, on peut enregistrer la réservation
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            # rediriger vers une page de confirmation
            return redirect('booking_success')
    else:
        form = BookingForm()
        # Pré-remplir avec données stockées dans la session si existantes
        if request.user.is_authenticated and 'booking_data' in request.session:
            form = BookingForm(initial=request.session.pop('booking_data'))
            
    return render(request, 'bookings/booking_form.html', {'form': form})

@login_required
def booking_success(request):
    return render(request, 'bookings/booking_success.html')
