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
        platform = GigFinder.objects.filter(name="www.setlist.fm").first()

        # loop through all announcements of setlist that are ignored
        for ca in ConcertAnnouncement.objects.filter(gigfinder__name="www.setlist.fm").filter(ignore=True).filter(id__gt=0).order_by('-pk'):

            print("working on", ca, ca.pk)

            # fetch data from setlist
            headers = {"x-api-key": sk_api_key, "Accept": "application/json", "Accept-charset": "unicode-1-1"}
            url = "https://api.setlist.fm/rest/1.0/setlist/{0}".format(ca.gigfinder_concert_id)
            r = get(url, headers=headers)
            try:
                response = loads(r.text)
            except decoder.JSONDecodeError:
                response = {"message": "Limit Exceeded"}

            print(response)

            if "message" in response and response["message"] != "Limit Exceeded":
                try:

                    concert = self.map_platform_to_schema(response, ca.artist, ca.artist.mbid, platform.name)

                    if isinstance(concert, dict):
                        venue_name = "|".join([concert["venue"], concert["stad"], concert["land"], platform.name])
                        venue = Venue.objects.filter(raw_venue=venue_name).first()
                        if not venue:
                            venue = Venue.objects.filter(raw_venue=venue_name.replace("www.setlist.fm", "setlist")).first()
                        if not venue:
                            venue = Venue.objects.create(
                                raw_venue=venue_name[0:199],
                                raw_location="|".join([concert["stad"], concert["land"], platform.name])[0:199]
                            )
                            venue.save()

                        if concert["titel"] != ca.title:
                            ca.title = concert["titel"][0:199]
                        if concert["datum"] != ca.date:
                            ca.date = concert["datum"]
                        if venue != ca.raw_venue:
                            ca.raw_venue = venue
                        if concert["latitude"] != ca.latitude:
                            ca.latitude = concert["latitude"]
                        if concert["longitude"] != ca.longitude:
                            ca.longitude = concert["longitude"]
                        ca.last_seen_on = datetime.now()
                        ca.ignore = False
                        ca.save()

                        if ca.concert.ignore:
                            ca.concert.ignore = False
                            ca.concert.save()

                except KeyError as e:
                    print("\tno announcement found, setting it on ignore", ca.pk)
                    ca.ignore = True
                    ca.save(update_fields=['ignore'])

                    masterconcert = ca.concert
                    if masterconcert:
                        if masterconcert.concertannouncements().count() == 1:
                            print("\tthis is the only announcement for the related concert, so concert is ignored, as well", masterconcert.pk)
                            masterconcert.ignore = True
                            masterconcert.save(update_fields=["ignore"])
                        else:
                            print("\tother announcements confirm the related concert, so concert is retained", masterconcert.pk)

    def map_platform_to_schema(self, concert, band, mbid, other):
        stad = concert["venue"]["city"]["name"]
        state = concert["venue"]["city"]["stateCode"] if "stateCode" in concert["venue"]["city"] else None
        if state is not None and concert["venue"]["city"]["country"]["code"] in ["US", "Brazil", "Australia", "Canada"]:
            stad = stad + ", " + state
        return {
            "titel": concert["info"] if "info" in concert else band.name + " @ " + concert["venue"]["name"] + " in " + concert["venue"]["city"]["name"] + ", " + concert["venue"]["city"]["country"]["code"],
            "datum": dateparse(concert["eventDate"], ["%d-%m-%Y"]).date(),
            "artiest": concert["artist"]["name"],
            "artiest_id": concert["artist"]["url"],
            "artiest_mb_naam": band.name,
            "artiest_mb_id": mbid,
            "stad": stad,
            "land": concert["venue"]["city"]["country"]["code"],
            "venue": concert["venue"]["name"],
            "latitude": concert["venue"]["city"]["coords"]["lat"] if "lat" in concert["venue"]["city"]["coords"] else None,
            "longitude": concert["venue"]["city"]["coords"]["long"] if "long" in concert["venue"]["city"]["coords"] else None,
            "source": other,
            "event_id": concert["id"]
        }
