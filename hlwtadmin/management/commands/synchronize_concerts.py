from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue

from musicbrainzngs import set_useragent, search_artists, musicbrainz, get_artist_by_id
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from time import sleep

from json import decoder, loads, dumps
from dateparser import parse as dateparse
from time import sleep
from requests import get
from fake_useragent import UserAgent
from re import compile
from codecs import open
from bs4 import BeautifulSoup
import os

import bandsintown
from time import sleep
from urllib import parse as urlparse
from json import decoder
from pandas import Timestamp, DataFrame
from dateparser import parse as dateparse
from datetime import datetime
import requests


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        set_useragent("kunstenpunt", "0.1", "github.com/kunstenpunt")
        leecher_fb = FacebookScraper()
        leecher_bit = BandsInTownLeecher()
        for gfurl in GigFinderUrl.objects.all():
            print(gfurl.artist, gfurl.artist.mbid, gfurl.url, gfurl.gigfinder.name)
            if gfurl.gigfinder.name == "www.facebook.com" and gfurl.artist.exclude is not True:
                leecher_fb.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)
            if gfurl.gigfinder.name == "bandsintown.com" and gfurl.artist.exclude is not True:
                leecher_bit.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)


class PlatformLeecher(object):
    def __init__(self):
        try:
            with open("hlwtadmin/google_api_places_api_key.txt", "r") as f:
                self.google_places_api_key = f.read().strip()
        except FileNotFoundError:
            self.google_places_api_key = os.environ.get('GOOGLE_PLACES_API_KEY')

    def get_lat_lon_for_venue(self, venue, city, country):
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={0}&key={1}"
        venue_search = " ".join([venue, city, country])
        city_search = " ".join([city, country])
        try:
            result = loads(get(url.format(venue_search, self.google_places_api_key)).text)
        except Exception as e:
            result = {"status": "ZERO_RESULTS"}
        if result["status"] == "ZERO_RESULTS":
            try:
                result = loads(get(url.format(city_search, self.google_places_api_key)).text)
            except Exception as e:
                result = {"results": []}
        if len(result["results"]) > 0:
            if "types" in result["results"][0]:
                if "locality" in result["results"][0]["types"] or "postal_code" in result["results"][0]["types"]:
                    city = result["results"][0]["name"]
                    country = result["results"][0]["formatted_address"].split(", ")[-1]
            else:
                city = ", ".join(result["results"][0]["formatted_address"].split(", ")[1:-1])
                country = result["results"][0]["formatted_address"].split(", ")[-1]
            return {
                "lat": result["results"][0]["geometry"]["location"]["lat"],
                "lng": result["results"][0]["geometry"]["location"]["lng"],
                "city": city,
                "country": country
            }
        else:
            return {"lat": None, "lng": None, "city": None, "country": None}


class FacebookScraper(PlatformLeecher):
    def __init__(self):
        self.platform = "facebook"
        self.gf = GigFinder.objects.filter(name="www.facebook.com").first()
        self.ua = UserAgent()

    def _get_event_ids(self, url):
        print(url)
        regex = compile('href="/events/(\d+?)\?')
        headers = {'user-agent': self.ua.random}
        sleep(10.0)
        try:
            r = get(url, headers=headers)
        except Exception as e:
            print("exception", e)
            sleep(60.0)
            try:
                r = get(url, headers=headers)
            except Exception as e:
                print("exception", e)
                sleep(360)
                r = get(url, headers=headers)
        event_ids = regex.findall(r.text)
        return event_ids

    def _get_event(self, event_id, test_file=None, test=False):
        url = "http://mobile.facebook.com/events/" + event_id
        headers = {'user-agent': self.ua.random}
        r = """<html></html>"""
        if not test:
            sleep(5.0)
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
            location = self._get_location(ld)
            titel = ld["name"]
            event_data = {
                "event_id": event_id,
                "datum": datum,
                "land": location["country"][0],
                "stad": location["city"][0],
                "venue": location["venue"][0:199],
                "latitude": location["lat"],
                "longitude": location["lng"],
                "titel": titel[0:199]
            }
            print(event_data)
        except AttributeError:
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
        loc_info = self.get_lat_lon_for_venue(location_name, location_street, location_country)
        loc_info["venue"] = location_name[0:199]
        loc_info["city"] = location_street[0:199],
        loc_info["country"] = location_country[0:199],
        return loc_info

    def set_events_for_identifier(self, band, mbid, url):
        print(band, mbid, url)

        urls = ["http://mobile.facebook" + "facebook".join(url.split("facebook")[1:]) + "/events"]

        for url in urls:
            event_ids = self._get_event_ids(url)

            events = []
            for event_id in event_ids:
                print("grabbing raw data for", event_id)
                concert = self._get_event(event_id)
                events.append(concert)

            if events:
                for concert in events:
                    if isinstance(concert, dict) and "event_id" in concert:
                        if not ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first():
                            venue_name = "|".join([concert["venue"], concert["stad"], concert["land"], self.platform])
                            venue = Venue.objects.filter(raw_venue=venue_name).first()
                            if not venue:
                                venue = Venue.objects.create(
                                    raw_venue=venue_name,
                                    raw_location="|".join([concert["stad"], concert["land"], self.platform])
                                )
                                venue.save()

                            ca = ConcertAnnouncement.objects.create(
                                title=concert["titel"],
                                artist=Artist.objects.filter(mbid=mbid).first(),
                                date=concert["datum"].isoformat(),
                                gigfinder=self.gf,
                                gigfinder_concert_id=concert["event_id"],
                                last_seen_on=datetime.now(),
                                raw_venue=venue,
                                ignore=False,
                                latitude=concert["latitude"],
                                longitude=concert["longitude"]
                            )
                            ca.save()


class BandsInTownLeecher(PlatformLeecher):
    def __init__(self):
        super().__init__()
        self.bitc = bandsintown.Client("kunstenpunt")
        self.platform = "bandsintown"
        self.gf = GigFinder.objects.filter(name="bandsintown.com").first()

    def set_events_for_identifier(self, band, mbid, url):
        period = "1900-01-01,2050-01-01"
        bandnaam = urlparse.unquote(url.split("/")[-1].split("?came_from")[0])
        events = None
        trials = 0
        while events is None and trials < 10:
            trials += 1
            try:
                try:
                    events = self.bitc.artists_events(bandnaam, date=period)
                except requests.exceptions.ConnectionError:
                    events = None
                if events is not None:
                    while "errors" in events:
                        print(events["errors"])
                        if "Rate limit exceeded" in events["errors"]:
                            print("one moment!")
                            sleep(60.0)
                            events = self.bitc.artists_events(bandnaam, date=period)
                        else:
                            events = []
            except decoder.JSONDecodeError:
                events = None

        if events:
            for concert in events:
                if isinstance(concert, dict):
                    concert = self.map_platform_to_schema(concert, band, mbid, {})
                    print(concert)
                    if not ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first():
                        venue_name = "|".join([concert["venue"], concert["stad"], concert["land"], self.platform])
                        venue = Venue.objects.filter(raw_venue=venue_name).first()
                        if not venue:
                            venue = Venue.objects.create(
                                raw_venue=venue_name[0:199],
                                raw_location="|".join([concert["stad"], concert["land"], self.platform])[0:199]
                            )
                            venue.save()

                        ca = ConcertAnnouncement.objects.create(
                            title=concert["titel"][0:199],
                            artist=Artist.objects.filter(mbid=mbid).first(),
                            date=concert["datum"].isoformat(),
                            gigfinder=self.gf,
                            gigfinder_concert_id=concert["event_id"],
                            last_seen_on=datetime.now(),
                            raw_venue=venue,
                            ignore=False,
                            latitude=concert["latitude"],
                            longitude=concert["longitude"]
                        )
                        ca.save()

    def map_platform_to_schema(self, concert, band, mbid, other):
        region = concert["venue"]["region"].strip() if "region" in concert["venue"] else None
        stad = (concert["venue"]["city"]).strip()
        if region is not None and (concert["venue"]["country"]).strip() in ["Ac United States", "United States", "Canada", "Brazil", "Australia"]:
            stad = stad + ", " + region.strip()
        return {
            "datum": dateparse(concert["datetime"]).date(),
            "land": (concert["venue"]["country"]).strip(),
            "stad": stad,
            "venue": (concert["venue"]["name"]).strip() if "name" in concert["venue"] else None,
            "titel": (str(band) + " - " + str((concert["venue"]["name"]).strip()) if "name" in concert["venue"] else None) + "," + dateparse(concert["datetime"]).date().isoformat() + (concert["description"]).strip(),
            "artiest": band,
            "artiest_mb_naam": band,
            "artiest_id": "bandsintown_" + str(concert["artist_id"]),
            "artiest_mb_id": mbid,
            "event_id": str(concert["id"]),
            "latitude": concert["venue"]["latitude"] if "latitude" in concert["venue"] else None,
            "longitude": concert["venue"]["longitude"] if "longitude" in concert["venue"] else None,
            "source": self.platform
        }

    @staticmethod
    def __get_artist_naam(concert):
        for artist in concert["artists"]:
            if artist["id"] == concert["artist_id"]:
                return artist["name"]
