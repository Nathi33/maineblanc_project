from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Supprime ou anonymise les réservations de plus de 10 ans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--anonymize',
            action='store_true',
            help='Anonymise les réservations au lieu de les supprimer'
        )

    def handle(self, *args, **options):
        # Define the limit date (10 years ago)
        limit_date = timezone.now() - timedelta(days=10*365)
        anonymize = options['anonymize']

        old_bookings = Booking.objects.filter(created_at__lt=limit_date)
        total = old_bookings.count()

        if total == 0:
            self.stdout.write("Aucune réservation ancienne à traiter.")
            return

        if anonymize:
            old_bookings.update(
                last_name='Anonyme',
                first_name='Anonyme',
                address='Anonyme',
                postal_code='00000',
                city='Anonyme',
                phone='0000000000',
                email='anonyme@example.com'
            )
            self.stdout.write(f"{total} réservations ont été anonymisées.")
        else:
            deleted_count, _ = old_bookings.delete()
            self.stdout.write(f"{deleted_count} réservations ont été supprimées.")
