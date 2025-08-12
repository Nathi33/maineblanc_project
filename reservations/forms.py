from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class ReservationRequestForm(forms.Form):
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
            'id': 'start_date', 
            'type': 'date', 
            'required': True,
            'min': timezone.localdate().strftime('%Y-%m-%d')
            })
    )
    end_date = forms.DateField(
        label=_("Date de départ"),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'end_date',
            'type': 'date',
            'required': True,
            'min': timezone.localdate().strftime('%Y-%m-%d')
        })
    )

    ACCOMMODATION_CHOICES = [
        ('', _("Choisissez un type")),
        ('tente', _("Tente / Voiture tente")),
        ('caravane', _("Caravane / Fourgon aménagé / Van")),
        ('camping_car', _("Camping-car")),
        ('mobil_home', _("Mobil-home"))
    ]
    accommodation_type = forms.ChoiceField(
        label=_("Type d'hébergement"),
        choices=ACCOMMODATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'accommodation_type', 'required': True})
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


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        errors = []

        # Vérifie que la date d'arrivée ne soit pas passée
        if start_date and start_date < today:
            errors.append(_("La date d'arrivée ne peut pas être antérieure à aujourd'hui."))

        # Vérifie que la date de départ ne soit pas antérieure à la date d'arrivée
        if start_date and end_date and end_date <= start_date:
            errors.append(_("La date de départ doit être postérieure à la date d'arrivée."))

        if errors:
            raise forms.ValidationError(errors)
        
        return cleaned_data