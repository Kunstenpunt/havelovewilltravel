from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Organisation

from musicbrainzngs import set_useragent, search_artists, musicbrainz, get_artist_by_id
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from time import sleep

from django.db.models import Avg, Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        count = 0
        for org in Organisation.objects.annotate(num_venues=Count('venue__raw_location', distinct=True)).filter(num_venues__gte=2):
            venuelocs = set([", ".join(loc.split("|")[-3:-1]) for loc in org.venue_set.all().values_list('raw_location', flat=True)])
            if len(venuelocs) > 1:
                count += 1
        print(count)
