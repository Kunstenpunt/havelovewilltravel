from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Organisation, RelationConcertOrganisation

from musicbrainzngs import set_useragent, search_artists, musicbrainz, get_artist_by_id
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from time import sleep

from django.db.models import Avg, Count

import pycountry, unicodedata


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def strip_accents(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')

    def norm(self, loc):

        translate = {
            "Nederland": "Netherlands",
            "België": "Belgium",
            "Duitsland": "Germany",
            "Zwitserland": "CH",
            "UK": "United Kingdom",
            "Antwerpen": "Antwerp",
            "Gent": "Ghent",
            "Wien": "Vienna",
            "Wenen": "Vienna",
            "Parijs": "Paris",
            "Brussel": "Brussels",
            "Bruxelles": "Brussels",
            "Den Haag": "The Hague",
            "München": "Munich",
            "Den Bosch": "'s-Hertogenbosch",
            "Brugge": "Bruges",
            "United Kingdom Of Great Britain And Northern Ireland": "GB",
            "The Netherlands": "NL",
            "Londen": "London",
            "Engeland": "GB",
        }
        country = loc.split("|")[-2]
        country = translate[country] if country in translate else country
        try:
            country = pycountry.countries.get(name=country).alpha_2
        except AttributeError:
            pass
        city = loc.split("|")[-3].split(",")[0].replace("-", " ")
        city = translate[city] if city in translate else city
        return self.strip_accents(city.lower()), country

    def handle(self, *args, **options):
        count = 0
        for org in Organisation.objects.annotate(num_venues=Count('venue__raw_location', distinct=True)).filter(num_venues__gte=2):
            venuelocs = set([self.norm(loc) for loc in org.venue_set.all().values_list('raw_location', flat=True)])
            if len(venuelocs) > 1:
                print(count + 1, org, org.pk)
                # print("\t", venuelocs)
                # print("\t\t", org.venue_set.all())
                # split = input("Should I split this?")
                # if split == "y":
                #     RelationConcertOrganisation.objects.filter(organisation=org).delete()
                #     for venue in org.venue_set.all():
                #         venue.organisation = None
                #         venue.save()
                print("\n---\n\n")
        print(count)
