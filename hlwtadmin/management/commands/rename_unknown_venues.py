from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from re import sub, IGNORECASE

from pandas import read_excel


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(name__icontains="unknown venue"):
            if org.location:
                name = "Unknown Venue in " + str(org.location)
            else:
                name = "Unknown Venue in Unknown Location"
            print(org.name, "to be renamed to", name)
            org.name = name
            org.save(update_fields=['name'])
