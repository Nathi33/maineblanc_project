from django import forms
from .models import Booking
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ----------------------------
# Formulaire réservation : Clients
# ----------------------------
class BookingFormClassic(forms.ModelForm):
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
            'start_date', 'end_date',
            ]
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
        """
        Validation personnalisée :
        - La date d'arrivée ne peut pas être antérieure à aujourd'hui.
        - La date de départ doit être postérieure à la date d'arrivée.
        - Champs conditionnels obligatoires selon type d'emplacement et électricité
        """
        cleaned_data = super().clean()

        # Validation des dates
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        if start_date and start_date < today:
            self.add_error("start_date", _("La date d'arrivée ne peut pas être antérieure à aujourd'hui."))
        if start_date and end_date and start_date > end_date:
            self.add_error("end_date", _("La date de départ doit être postérieure à la date d'arrivée."))

        # Gestion du type d'emplacement et sous-types
        booking_subtype = cleaned_data.get("booking_type")
        electricity = cleaned_data.get("electricity")

        # Mapping des sous-types vers les types principaux
        subtype_to_main = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        if booking_subtype:
            # Conversion vers le type principal
            main_type = subtype_to_main.get(booking_subtype, booking_subtype)
            cleaned_data["booking_type"] = main_type
            # On garde le choix précis dans un champ "booking_subtype"
            cleaned_data["booking_subtype"] = booking_subtype
            # Ajout d'une version lisible pour le template
            cleaned_data["booking_subtype_display"] = booking_subtype.replace("_", " ").capitalize()
        else:
            self.add_error("booking_type", _("Le champ 'Type d'emplacement' est obligatoire."))

        # Champs conditionnels obligatoires selon le type principal
        if booking_subtype in ["caravan", "fourgon", "van", "motorhome"]:
            if not cleaned_data.get("vehicle_length"):
                self.add_error("vehicle_length", _("Le champ 'Longueur du véhicule' est obligatoire pour les caravanes et camping-cars."))

        if booking_subtype in ["tent", "car_tent"]:
            if not cleaned_data.get("tent_width"):
                self.add_error("tent_width", _("Le champ 'Largeur de la tente' est obligatoire pour les tentes."))
            if not cleaned_data.get("tent_length"):
                self.add_error("tent_length", _("Le champ 'Longueur de la tente' est obligatoire pour les tentes."))
        
        # Longueur du câble si électricité
        if electricity == "yes":
            cable_length = cleaned_data.get("cable_length")
            if not cable_length:
                self.add_error("cable_length", _("Le champ 'Longueur du câble' est obligatoire si l'électricité est incluse."))

        return cleaned_data


# ----------------------------
# Formulaire pour les coordonnées du client
# ----------------------------
class BookingDetailsForm(forms.Form):
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
    email = forms.EmailField(
        label=_("Adresse mail"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        label=_("Téléphone"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )