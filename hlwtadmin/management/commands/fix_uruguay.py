from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        us = Country.objects.filter(name="United States").first()
        print(us)
        for loc in Location.objects.filter(country__name="Uruguay").exclude(verified=True):
            print("changing", loc)
            loc.country = us
            loc.save()
