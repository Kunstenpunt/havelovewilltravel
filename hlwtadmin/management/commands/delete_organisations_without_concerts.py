from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(relationconcertorganisation__isnull=True).filter(venue__concertannouncement__isnull=True).exclude(verified=True):
            venues = Venue.objects.filter(organisation=org)
            if len(venues) < 2:
                if len(venues) == 1:
                    print("deleting venue", venues[0], venues[0].pk)
                    venues[0].delete()
                print("deleting organisation", org, org.pk)
                org.delete()
