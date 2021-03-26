from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models.functions import Length

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(until_date__isnull=False):
            for ca in concert.concertannouncements():
                if "facebook" in ca.gigfinder.name:
                    if ca.until_date is None:
                        print(concert, concert.pk, ca, ca.pk)
                        print("updating until date")
                        input()
                        concert.date = ca.date
                        concert.until_date = None
                        concert.save(update_fields=["until_date"])

