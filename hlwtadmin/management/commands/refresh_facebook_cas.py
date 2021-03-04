from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from requests import get
from json import loads, dumps

from dateparser import parse as dateparse
from datetime import datetime

import time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from re import sub


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.platform = GigFinder.objects.filter(name="www.facebook.com").first()
        self.ua = UserAgent()

        # loop through all announcements of songkick that are not ignored
        for concertannouncement in ConcertAnnouncement.objects.filter(gigfinder__name="www.facebook.com"):

            print("working on", concertannouncement, concertannouncement.pk)
            time.sleep(3)
            # fetch data from facebook
            concert = self.get_event(concertannouncement.gigfinder_concert_id)
            print("data", concert)
            if concert:
                if concert["titel"] != concertannouncement.title:
                    concertannouncement.title = concert["titel"]
                if concert["datum"] != concertannouncement.date:
                    concertannouncement.date = concert["datum"]
                if concert["einddatum"] != concertannouncement.until_date:
                    concertannouncement.until_date = concert["einddatum"]
                if concert["latitude"] != concertannouncement.latitude:
                    concertannouncement.latitude = concert["latitude"]
                if concert["longitude"] != concertannouncement.longitude:
                    concertannouncement.longitude = concert["longitude"]
                if concert["description"] != concertannouncement.description:
                    concertannouncement.description = concert["description"]
                concertannouncement.last_seen_on = datetime.now()
                print("ca geupdated", concertannouncement, concertannouncement.pk)
                concertannouncement.save(update_fields=["description", "latitude", "longitude", "title", "date", "until_date", "last_seen_on"])

    def get_event(self, event_id, test_file=None, test=False):
        url = "http://mobile.facebook.com/events/" + str(event_id)
        print(url)
        headers = {'user-agent': self.ua.firefox}
        r = """<html></html>"""
        if not test:
            time.sleep(5.0)
            try:
                r = get(url, headers=headers).text
            except Exception as e:
                self._get_event(event_id, test_file, test)
        else:
            with open(test_file, "r", "utf-8") as f:
                r = f.read()
        soup = BeautifulSoup(r, 'html.parser')
        try:
            ld = loads(soup.find("script", {"type": "application/ld+json"}).text)
            datum = dateparse(ld["startDate"]).date()
            einddatum = dateparse(ld["endDate"]).date() if "endDate" in ld else None
            location = self._get_location(ld)
            titel = ld["name"]
            desc = ld["description"]
            event_data = {
                "event_id": event_id,
                "datum": datum,
                "einddatum": einddatum,
                "land": location["country"],
                "stad": location["city"],
                "venue": location["venue"],
                "latitude": location["lat"],
                "longitude": location["lng"],
                "titel": titel[0:199],
                "description": desc
            }
            print("event", event_data)
        except AttributeError as e:
            print("error", e)
            event_data = {}
        return event_data

    def _get_location(self, ld):
        try:
            location_name = ld["location"]["name"]
        except KeyError:
            location_name = ""
        try:
            location_street = ld["location"]["address"]["addressLocality"]
        except KeyError:
            location_street = ""
        try:
            location_country = ld["location"]["address"]["addressCountry"]
        except KeyError:
            location_country = ""
        loc_info = {
            "lat": None,
            "lng": None,
        }
        loc_info["venue"] = location_name[0:199]
        loc_info["city"] = location_street[0:199]
        loc_info["country"] = location_country[0:199]
        return loc_info
