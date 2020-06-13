from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from collections import Counter


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for venue in Venue.objects.filter(raw_venue__endswith="songkick"):
            venue.raw_venue = venue.raw_venue.replace("|songkick", "|www.songkick.com")
            venue.raw_location = venue.raw_location.replace("|songkick", "|www.songkick.com")
            venue.save()

        for venue in Venue.objects.filter(raw_venue__endswith="bandsintown"):
            venue.raw_venue = venue.raw_venue.replace("|bandsintown", "|bandsintown.com")
            venue.raw_location = venue.raw_location.replace("|bandsintown", "|bandsintown.com")
            venue.save()

        for venue in Venue.objects.filter(raw_venue__endswith="facebook"):
            venue.raw_venue = venue.raw_venue.replace("|facebook", "|www.facebook.com")
            venue.raw_location = venue.raw_location.replace("|facebook", "|www.facebook.com")
            venue.save()
