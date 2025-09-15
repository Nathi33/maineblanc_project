from glob import escape
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class ReservationRequestForm(forms.Form):
    """
    Form to handle reservation requests from customers.

    Fields:
        - Customer info: name, first_name, address, postal_code, city, phone, email
        - Reservation dates: start_date, end_date
        - Accommodation details: accommodation_type, tent dimensions, vehicle_length
        - Guests: adults, children_over_8, children_under_8, pets
        - Electricity info: electricity, cable_length
        - Message: optional free text
    Security:
        - Fields are validated and escaped to prevent XSS
        - Conditional fields validated in `clean()`
    """

    name = forms.CharField(
        label=_("Nom"), max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'name', 'required': True})
    )
    first_name = forms.CharField(
        label=_("Prénom"), max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'first_name', 'required': True})
    )
    address = forms.CharField(
        label=_("Adresse"), max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'address', 'required': True})
    )
    postal_code = forms.CharField(
        label=_("Code postal"), max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'postal_code', 'required': True})
    )
    city = forms.CharField(
        label=_("Ville"), max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'city', 'required': True})
    )
    phone = forms.CharField(
        label=_("Téléphone"), max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'phone', 'required': True, 'type': 'tel'})
    )
    email = forms.EmailField(
        label=_("Adresse email"), max_length=255,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'email', 'required': True})
    )
    message = forms.CharField(
        label=_("Message"), 
        widget=forms.Textarea(attrs={'class': 'form-control message-form', 'id': 'message', 'rows': 4}),
        max_length=1000, 
        required=False
    )

    start_date = forms.DateField(
        label=_("Date d'arrivée"),
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'id': 'id_start_date', 
            'type': 'date', 
            'required': True,
            'min': timezone.localdate().strftime('%Y-%m-%d')
            })
    )
    end_date = forms.DateField(
        label=_("Date de départ"),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'id_end_date',
            'type': 'date',
            'required': True,
            'min': timezone.localdate().strftime('%Y-%m-%d')
        })
    )

    ACCOMMODATION_CHOICES = [
        ('', _("Choisissez un type")),
        ('tent', _("Tente")),
        ('car_tent', _("Voiture tente")),
        ('caravan', _("Caravane")),
        ('fourgon', _("Fourgon aménagé")),
        ('van', _("Van")),
        ('camping_car', _("Camping-car")),
        ('mobil-home', _("Mobil-home"))
    ]
    accommodation_type = forms.ChoiceField(
        label=_("Type d'hébergement"),
        choices=ACCOMMODATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'accommodation_type', 'required': True})
    )

    tent_length = forms.DecimalField(
        label=_("Longueur de la tente (m)"),
        required=False,
        min_value=1,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'tent_length'})
    )

    tent_width = forms.DecimalField(
        label=_("Largeur de la tente (m)"),
        required=False,
        min_value=1,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'tent_width'})
    )

    vehicle_length = forms.DecimalField(
        label=_("Longueur du véhicule (m)"),
        required=False,
        min_value=1,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'vehicle_length'})
    )

    adults = forms.ChoiceField(
        label=_("Adultes"),
        choices=[(i, i) for i in range(1, 11)],
        widget=forms.Select(attrs={
            'class': 'form-select', 
            'id': 'adults', 
            'required': True
        })                     
    )
    children_over_8 = forms.ChoiceField(
        label=_("+8 ans"),
        choices=[(i, i) for i in range(0, 11)],
        widget=forms.Select(attrs={
            'class': 'form-select', 
            'id': 'children_over_8', 
            'required': True
        })
    )
    children_under_8 = forms.ChoiceField(
        label=_("-8 ans"),
        choices=[(i, i) for i in range(0, 11)],
        widget=forms.Select(attrs={
            'class': 'form-select', 
            'id': 'children_under_8', 
            'required': True
        })
    )
    pets = forms.ChoiceField(
        label=_("Animaux"),
        choices=[(i, i) for i in range(0, 3)],
        widget=forms.Select(attrs={
            'class': 'form-select', 
            'id': 'pets', 
            'required': True
        })
    )

    ELECTRICITY_CHOICES = [
        ('yes', _("Avec électricité")),
        ('no', _("Sans électricité"))
    ]
    electricity = forms.ChoiceField(
        label=_("Électricité"), 
        choices=ELECTRICITY_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form--check-input'})
    )

    cable_length = forms.DecimalField(
        label=_("Longueur du câble électrique (m)"),
        required=False,
        min_value=1,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'cable_length'})
    )


    def clean(self):
        """
        Custom validation:
            - Validate dates (arrival < departure, not in past)
            - Validate conditional fields (tent dimensions, vehicle length, cable if electricity)
            - Escape free-text message to prevent XSS
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        accommodation_type = cleaned_data.get("accommodation_type")
        tent_length = cleaned_data.get("tent_length")
        tent_width = cleaned_data.get("tent_width")
        vehicle_length = cleaned_data.get("vehicle_length")

        electricity = cleaned_data.get("electricity")
        cable_length = cleaned_data.get("cable_length")

        message = cleaned_data.get("message")
        if message:
            cleaned_data['message'] = escape(message)

        errors = []

        if start_date and start_date < today:
            errors.append(_("La date d'arrivée ne peut pas être antérieure à aujourd'hui."))

        if start_date and end_date and end_date <= start_date:
            errors.append(_("La date de départ doit être postérieure à la date d'arrivée."))

        if accommodation_type in ['tent', 'car_tent']:
            if not tent_length or not tent_width:
                errors.append(_("La longueur et la largeur de la tente sont obligatoires pour le type d'hébergement sélectionné."))
        
        if accommodation_type in ['caravan', 'fourgon', 'van', 'camping_car']:
            if not vehicle_length:
                errors.append(_("La longueur du véhicule est obligatoire pour le type d'hébergement sélectionné."))

            if electricity == 'yes' and not cable_length:
                errors.append(_("La longueur du câble électrique est obligatoire si l'électricité est demandée."))

        if errors:
            raise forms.ValidationError(errors)
        
        return cleaned_data