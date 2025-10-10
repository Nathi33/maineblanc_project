from django import forms
from .models import Booking
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class BookingFormClassic(forms.ModelForm):
    """
    Client booking form.

    Main fields:
        - booking_type: campsite type (tent, caravan, camper, etc.)
        - start_date / end_date: arrival and departure dates
        - adults, children_over_8, children_under_8, pets: number of people and pets
        - electricity: whether electricity is required
        - cable_length: required if electricity is selected
        - tent_width / tent_length, vehicle_length: specific dimensions depending on type

    Security:
        - Dates cannot be in the past.
        - Conditional fields are validated based on campsite type.
        - All data is cleaned via clean() method.
    """
    BOOKING_TYPE_CHOICES_FOR_FORM = [
        ('tent', _('Tente')),
        ('car_tent', _('Voiture Tente')),
        ('caravan', _('Caravane')),
        ('fourgon', _('Fourgon')),
        ('van', _('Van')),
        ('camping_car', _('Camping-car')),
    ]

    SUBTYPE_TO_MAIN_TYPE = {
        'tent': 'tent',
        'car_tent': 'tent',
        'caravan': 'caravan',
        'fourgon': 'caravan',
        'van': 'caravan',
        'camping_car': 'camping_car',
    }

    ELECTRICITY_CHOICES = [
        ('yes', _("Avec électricité")),
        ('no', _("Sans électricité"))
    ]

    booking_type = forms.ChoiceField(
        choices=[('', _('--- Choisissez ---'))] + BOOKING_TYPE_CHOICES_FOR_FORM,
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
        widget=forms.Select(choices=[(i, i) for i in range(1, 7)], attrs={'class': 'form-select'}),
        label=_("Adultes"),
        required=True
    )
    
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
            'start_date', 'end_date',
            ]
        labels = {
            'vehicle_length': _("Longueur du véhicule (m)"),
            'tent_width': _("Largeur de la tente (m)"),
            'tent_length': _("Longueur de la tente (m)"),
            'children_over_8': _("Enfants +8 ans"),
            'children_under_8': _("Enfants -8 ans"),
            'pets': _("Animaux (2 max)"),
            'cable_length': _("Longueur du câble électrique (m)"),
        }
        widgets = {
            'vehicle_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tent_width': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tent_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'children_over_8': forms.Select(choices=[(i, i) for i in range(0, 6)], attrs={'class': 'form-select'}),
            'children_under_8': forms.Select(choices=[(i, i) for i in range(0, 6)], attrs={'class': 'form-select'}),
            'pets': forms.Select(choices=[(i, i) for i in range(0, 3)], attrs={'class': 'form-select'}),
            'cable_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


    def clean(self):
        """
        Custom validation:
            - Arrival date cannot be in the past.
            - Departure date must be after arrival.
            - Conditional fields are required depending on campsite type and electricity.
        """
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        # Ensure dates are provided
        if not start_date or not end_date:
            raise forms.ValidationError(_("Les dates de réservations sont requises."))

        # Date validation
        if start_date < today:
            raise forms.ValidationError(_("La date d'arrivée ne peut pas être antérieure à aujourd'hui."))
        if start_date > end_date:
            raise forms.ValidationError(_("La date de départ doit être postérieure à la date d'arrivée."))

        # Check the maximum length of stay (3 weeks = 21 days)
        duration = (end_date - start_date).days
        if duration > 21:
            raise forms.ValidationError(
                _("La durée maximale de séjour est de 3 semaines. "
                  "Pour toute demande particulière, merci de contacter directement le camping.")
            )

        # Type and subtype validation
        booking_subtype = cleaned_data.get("booking_type")
        electricity = cleaned_data.get("electricity")
        subtype_to_main = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        if booking_subtype:
            main_type = subtype_to_main.get(booking_subtype, booking_subtype)
            cleaned_data["booking_type"] = main_type
            cleaned_data["booking_subtype"] = booking_subtype
            cleaned_data["booking_subtype_display"] = booking_subtype.replace("_", " ").capitalize()
        else:
            self.add_error("booking_type", _("Le champ 'Type d'emplacement' est obligatoire."))

        # Conditional required fields
        if booking_subtype in ["caravan", "fourgon", "van", "camping_car"]:
            if not cleaned_data.get("vehicle_length"):
                self.add_error("vehicle_length", _("Le champ 'Longueur du véhicule' est obligatoire pour les caravanes et camping-cars."))

        if booking_subtype in ["tent", "car_tent"]:
            if not cleaned_data.get("tent_width"):
                self.add_error("tent_width", _("Le champ 'Largeur de la tente' est obligatoire pour les tentes."))
            if not cleaned_data.get("tent_length"):
                self.add_error("tent_length", _("Le champ 'Longueur de la tente' est obligatoire pour les tentes."))
        
        if electricity == "yes":
            cable_length = cleaned_data.get("cable_length")
            if not cable_length:
                self.add_error("cable_length", _("Le champ 'Longueur du câble' est obligatoire si l'électricité est incluse."))

        # Total people validation
        adults = cleaned_data.get("adults") or 0
        children_over_8 = cleaned_data.get("children_over_8") or 0
        children_under_8 = cleaned_data.get("children_under_8") or 0
        total_people = adults + children_over_8 + children_under_8

        if total_people > 6:
            raise forms.ValidationError(
                _("Le nombre maximum de personnes (adultes et enfants) ne peut pas dépasser 6."
                  " Pour toute demande particulière, merci de contacter directement le camping.")
            )

        return cleaned_data


class BookingDetailsForm(forms.Form):
    """
    Client personal details form.

    Security:
        - Email field validated automatically.
        - Maximum length for all text fields to prevent injection.
        - All data cleaned via cleaned_data.
    """
    last_name = forms.CharField(
        max_length=100,
        label=_("Nom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=100,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        max_length=255,
        label=_("Adresse"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(
        max_length=20,
        label=_("Code postal"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        max_length=100,
        label=_("Ville"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        label=_("Téléphone"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=255,
        label=_("Adresse mail"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        """
        Centralized cleaning and validation:
        - Strips leading/trailing spaces for all text fields.
        - Normalizes email to lowercase.
        - Validates phone number contains only digits, spaces, +, -, ().
        """
        cleaned_data = super().clean()

        # Normalize text fields
        for field in ["first_name", "last_name", "address", "postal_code", "city"]:
            value = cleaned_data.get(field)
            if value:
                cleaned_data[field] = value.strip()

        # Normalize and validate email
        email = cleaned_data.get("email")
        if email:
            cleaned_data["email"] = email.strip().lower()

        # Validate phone
        phone = cleaned_data.get("phone")
        if phone:
            phone = phone.strip()
            import re
            if not re.match(r'^[\d+\-\s()]+$', phone):
                self.add_error("phone", _("Enter a valid phone number."))
            else:
                cleaned_data["phone"] = phone

        return cleaned_data