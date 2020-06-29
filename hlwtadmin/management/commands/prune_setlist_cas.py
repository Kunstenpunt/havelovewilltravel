from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from json import decoder, loads, dumps

from requests import get

from dateparser import parse as dateparse
from datetime import datetime

import time


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        sk_api_key = GigFinder.objects.filter(name="www.setlist.fm").first().api_key

        # loop through all announcements of setlist that are ignored
        print(ConcertAnnouncement.objects.filter(gigfinder__name="www.setlist.fm").filter(ignore=True).filter(id__gt=0).count())
        for ca in ConcertAnnouncement.objects.filter(gigfinder__name="www.setlist.fm").filter(ignore=True).filter(id__gt=0).order_by('-pk'):

            print("working on", ca, ca.pk)

            # fetch data from setlist
            headers = {"x-api-key": sk_api_key, "Accept": "application/json", "Accept-charset": "unicode-1-1"}
            url = "https://api.setlist.fm/rest/1.0/setlist/{0}".format(ca.gigfinder_concert_id)
            r = get(url, headers=headers)
            print(r.status_code)
            print(r.text)

            if r.status_code != 200:
                print("\tno announcement found, uncoupling from concert and deleting announcement", ca.pk)
                ca.concert = None
                ca.save(update_fields=['concert'])
                ca.delete()
