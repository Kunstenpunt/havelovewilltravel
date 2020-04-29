from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Organisation

from musicbrainzngs import set_useragent, search_artists, musicbrainz, get_artist_by_id
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from time import sleep

from django.db.models import Avg, Count

import pycountry


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def norm(self, loc):

        translate = {
            "Nederland": "Netherlands",
            "België": "Belgium",
            "Duitsland": "Germany",
            "UK": "United Kingdom",
            "Antwerpen": "Antwerp",
            "Gent": "Ghent",
            "Wien": "Vienna",
            "Wenen": "Vienna",
            "Parijs": "Paris",
            "Brussel": "Brussels"
        }
        country = loc.split("|")[-2]
        country = translate[country] if country in translate else country
        try:
            country = pycountry.countries.get(name=country).alpha_2
        except AttributeError:
            pass
        city = loc.split("|")[-3]
        city = translate[city] if city in translate else city
        return city, country

    def handle(self, *args, **options):
        count = 0
        for org in Organisation.objects.annotate(num_venues=Count('venue__raw_location', distinct=True)).filter(num_venues__gte=2):
            venuelocs = set([self.norm(loc) for loc in org.venue_set.all().values_list('raw_location', flat=True)])
            if len(venuelocs) > 1:
                print(venuelocs)
                count += 1
        print(count)
