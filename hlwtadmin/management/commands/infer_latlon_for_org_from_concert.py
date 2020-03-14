from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(latitude__isnull=True):
            print(org, org.latitude, org.longitude)
            rel = RelationConcertOrganisation.objects.filter(organisation=org).first()
            if rel:
                lat = rel.concert.latitude
                lon = rel.concert.longitude
                if not lat:
                    lat = org.location.latitude
                    lon = org.location.longitude
                org.latitude = lat
                org.longitude = lon
                org.save()
                print(">>>", org, org.latitude, org.longitude)
