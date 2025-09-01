from django import forms
from .models import Booking
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class BookingForm(forms.ModelForm):
    booking_type = forms.ChoiceField(
        choices=[('', _('--- Choisissez ---'))] + Booking.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Type d'emplacement"),
        required=True
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.localdate().isoformat()}),
        label=_("Date d'arrivée"),
        required=True
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=_("Date de départ"),
        required=True
    )

    adults = forms.IntegerField(
        widget=forms.Select(choices=[(i, i) for i in range(1, 11)], attrs={'class': 'form-select'}),
        label=_("Adultes"),
        required=True
    )

    ELECTRICITY_CHOICES = [
        ('yes', _("Avec électricité")),
        ('no', _("Sans électricité"))
    ]
    
    electricity = forms.ChoiceField(
        choices=ELECTRICITY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Électricité"),
        required=True
    )

    class Meta:
        model = Booking
        fields = [
            'booking_type', 'vehicle_length', 'tent_width', 'tent_length',
            'adults', 'children_over_8', 'children_under_8', 'pets',
            'electricity', 'cable_length',
            'start_date', 'end_date']
        labels = {
            'vehicle_length': _("Longueur du véhicule (m)"),
            'tent_width': _("Largeur de la tente (m)"),
            'tent_length': _("Longueur de la tente (m)"),
            'children_over_8': _("Enfants +8 ans"),
            'children_under_8': _("Enfants -8 ans"),
            'pets': _("Animaux"),
            'cable_length': _("Longueur du câble électrique (m)"),
        }
        widgets = {
            'vehicle_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'tent_width': forms.NumberInput(attrs={'class': 'form-control'}),
            'tent_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'children_over_8': forms.Select(choices=[(i, i) for i in range(0, 11)], attrs={'class': 'form-select'}),
            'children_under_8': forms.Select(choices=[(i, i) for i in range(0, 11)], attrs={'class': 'form-select'}),
            'pets': forms.Select(choices=[(i, i) for i in range(0, 3)], attrs={'class': 'form-select'}),
            'cable_length': forms.NumberInput(attrs={'class': 'form-control'}),
        }


def clean(self):
    cleaned_data = super().clean()
    start_date = cleaned_data.get("start_date")
    end_date = cleaned_data.get("end_date")
    today = timezone.localdate()

    # Vérifie que la date d'arrivée est postérieure à la date d'aujourd'hui
    if start_date and start_date < today:
        self.add_error("start_date", _("La date d'arrivée ne peut pas être antérieure à aujourd'hui."))

    # Vérifie que la date de départ est postérieure à la date d'arrivée
    if start_date and end_date:
        if start_date > end_date:
            self.add_error("end_date", _("La date de départ doit être postérieure à la date d'arrivée."))

    return cleaned_data