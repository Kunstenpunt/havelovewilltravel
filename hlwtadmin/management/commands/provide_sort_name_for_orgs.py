from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from re import sub, IGNORECASE

from pandas import read_excel


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            print(org.name)
            sort_name = org.name
            sort_name = sub("^\s", "", sort_name)
            sort_name = sub("^the", "", sort_name, flags=IGNORECASE)
            sort_name = sub("20\d\d$", "", sort_name)
            sort_name = sub("\bfestival$", "", sort_name, flags=IGNORECASE)
            sort_name = sub("\bsold out\b", "", sort_name, flags=IGNORECASE)
            sort_name = sub("^\d\d:\d\d\d-\d", "", sort_name)
            org.sort_name = sort_name
            print(sort_name)
            org.save(update_fields=['sort_name'])
