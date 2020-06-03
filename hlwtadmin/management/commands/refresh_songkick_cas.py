from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from requests import get
from json import loads

from dateparser import parse as dateparse


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        sk_api_key = GigFinder.objects.filter(name="www.songkick.com").first().api_key

        # loop through all announcements of songkick that are not ignored
        for ca in ConcertAnnouncement.objects.filter(gigfinder__name="www.songkick.com").exclude(ignore=True):

            # fetch data from songkick
            sk_url = "https://api.songkick.com/api/3.0/events/" + ca.gigfinder_concert_id +".json?apikey=" + sk_api_key
            html = get(sk_url).text
            data = loads(html) if html is not None else {}
            result = data["resultsPage"]["results"]["event"]

            # if is festival or has end date
            if result["type"] == "Festival" or "end" in result:
                ca.is_festival = result["type"] == "Festival"
                ca.until_date = dateparse(result["end"]["date"]).date() if "end" in result else None

                # if is festival and has unknown in venue name, change venue to festival name
                if result["type"] == "Festival" and "unknown" in ca.raw_venue.raw_venue.lower():
                    venue_name = "|".join([result["displayName"], ",".join(result["location"]["city"].split(",")[0:-1]), result["location"]["city"].split(",")[-1], self.platform])
                    venue = Venue.objects.filter(raw_venue=venue_name).first()
                    if not venue:
                        venue = Venue.objects.create(
                            raw_venue=venue_name[0:199],
                            raw_location="|".join([",".join(result["location"]["city"].split(",")[0:-1]), result["location"]["city"].split(",")[-1], self.platform])[0:199]
                        )
                        venue.save()


                    print("about to change", ca.pk, "and setting is_festival to", result["type"] == "Festival", "until_date to", dateparse(result["end"]["date"]).date() if "end" in result else None, "and raw_venue to", venue)
                    input()

                    # decouple raw venue from organisation
                    ca.raw_venue.organisation = None
                    ca.raw_venue.save()

                    # decouple raw venue from concert announcement
                    ca.raw_venue = None

                    # couple new raw venue to announcement
                    ca.raw_venue = venue

                    # update announcement
                    ca.save(update_fields=['raw_venue', 'until_date', 'is_festival'])
