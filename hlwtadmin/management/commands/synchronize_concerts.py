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

from math import ceil


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        set_useragent("kunstenpunt", "0.1", "github.com/kunstenpunt")
        leecher_fb = FacebookScraper()
        leecher_bit = BandsInTownLeecher()
        leecher_setlist = SetlistFmLeecher()
        leecher_songkick = SongkickLeecher()
        for gfurl in GigFinderUrl.objects.all():
            print(gfurl.artist, gfurl.artist.mbid, gfurl.url, gfurl.gigfinder.name)
            if gfurl.gigfinder.name == "www.facebook.com" and gfurl.artist.exclude is not True:
                leecher_fb.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)
            if gfurl.gigfinder.name == "bandsintown.com" and gfurl.artist.exclude is not True:
                leecher_bit.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)
            if gfurl.gigfinder.name == "www.setlist.fm" and gfurl.artist.exclude is not True:
                leecher_setlist.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)
            if gfurl.gigfinder.name == "www.songkick.com" and gfurl.artist.exclude is not True:
                leecher_songkick.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)
            gfurl.last_synchronized = datetime.now()
            gfurl.save(update_fields=['last_synchronize'])


class PlatformLeecher(object):
    def __init__(self):
        try:
            with open("hlwtadmin/google_api_places_api_key.txt", "r") as f:
                self.google_places_api_key = f.read().strip()
        except FileNotFoundError:
            self.google_places_api_key = os.environ.get('GOOGLE_PLACES_API_KEY').strip("'")
        print("platform leecher api key google places", self.google_places_api_key)

    def get_lat_lon_for_venue(self, venue, city, country):
        print("init locsearch", venue, city, country)
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={0}&key={1}"
        venue_search = " ".join([venue, city, country])
        city_search = " ".join([city, country])
        print("locsearch", url.format(venue_search, self.google_places_api_key))
        try:
            result = loads(get(url.format(venue_search, self.google_places_api_key)).text)
        except Exception as e:
            print("exception", e)
            result = {"status": "ZERO_RESULTS"}
        if result["status"] == "ZERO_RESULTS":
            try:
                result = loads(get(url.format(city_search, self.google_places_api_key)).text)
            except Exception as e:
                print("exception", e)
                result = {"results": []}
        if len(result["results"]) > 0:
            print("result found", result)
            if "types" in result["results"][0]:
                if "locality" in result["results"][0]["types"] or "postal_code" in result["results"][0]["types"]:
                    city = result["results"][0]["name"]
                    country = result["results"][0]["formatted_address"].split(", ")[-1]
            else:
                city = ", ".join(result["results"][0]["formatted_address"].split(", ")[1:-1])
                country = result["results"][0]["formatted_address"].split(", ")[-1]
            print("ready to send back")
            return {
                "lat": result["results"][0]["geometry"]["location"]["lat"],
                "lng": result["results"][0]["geometry"]["location"]["lng"],
                "city": city,
                "country": country
            }
        else:
            print("nothing found", result)
            return {"lat": None, "lng": None, "city": None, "country": None}


class FacebookScraper(PlatformLeecher):
    def __init__(self):
        super(FacebookScraper, self).__init__()
        self.platform = "facebook"
        self.gf = GigFinder.objects.filter(name="www.facebook.com").first()
        self.ua = UserAgent()

    def _get_event_ids(self, url):
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
            print("looking for json ld")
            ld = loads(soup.find("script", {"type": "application/ld+json"}).text)
            datum = dateparse(ld["startDate"]).date()
            print("moving to locsearch")
            location = self._get_location(ld)
            print("location is", location)
            titel = ld["name"]
            event_data = {
                "event_id": event_id,
                "datum": datum,
                "land": location["country"],
                "stad": location["city"],
                "venue": location["venue"],
                "latitude": location["lat"],
                "longitude": location["lng"],
                "titel": titel[0:199]
            }
            print("event data", event_data)
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
        loc_info = self.get_lat_lon_for_venue(location_name, location_street, location_country)
        loc_info["venue"] = location_name[0:199]
        loc_info["city"] = location_street[0:199]
        loc_info["country"] = location_country[0:199]
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
                        concertannouncement = ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first()
                        if not concertannouncement:
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
                        else:
                            if concert["titel"] != concertannouncement.title:
                                concertannouncement.title = concert["titel"]
                            if concert["datum"] != concertannouncement.date:
                                concertannouncement.date = concert["datum"]
                            if concert["latitude"] != concertannouncement.latitude:
                                concertannouncement.latitude = concert["latitude"]
                            if concert["longitude"] != concertannouncement.longitude:
                                concertannouncement.longitude = concert["longitude"]
                            concertannouncement.last_seen_on = datetime.now()
                            concertannouncement.save()


class BandsInTownLeecher(PlatformLeecher):
    def __init__(self):
        super(BandsInTownLeecher, self).__init__()
        self.bitc = bandsintown.Client("kunstenpunt")
        self.platform = "bandsintown.com"
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
                    concertannouncement = ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first()
                    if not concertannouncement:
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
                    else:
                        if concert["titel"] != concertannouncement.title:
                            concertannouncement.title = concert["titel"][0:199]
                        if concert["datum"] != concertannouncement.date:
                            concertannouncement.date = concert["datum"]
                        if concert["latitude"] != concertannouncement.latitude:
                            concertannouncement.latitude = concert["latitude"]
                        if concert["longitude"] != concertannouncement.longitude:
                            concertannouncement.longitude = concert["longitude"]
                        concertannouncement.last_seen_on = datetime.now()
                        concertannouncement.save()

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


class SetlistFmLeecher(PlatformLeecher):
    def __init__(self):
        super(SetlistFmLeecher, self).__init__()
        self.gf = GigFinder.objects.filter(name="www.setlist.fm").first()
        try:
            with open("hlwtadmin/setlist_api_key.txt", "r") as f:
                self.platform_access_granter = f.read()
        except FileNotFoundError:
            self.platform_access_granter = self.gf.api_key
        self.platform = "www.setlist.fm" # base_url is www.setlist.fm/a/0/b-
        print("setlistfm api", self.platform_access_granter)

    def set_events_for_identifier(self, band, mbid, url):
        events = []
        total_hits = 1
        p = 1
        retrieved_hits = 0
        while retrieved_hits < total_hits:
            headers = {"x-api-key": self.platform_access_granter, "Accept": "application/json"}
            r = get("https://api.setlist.fm/rest/1.0/artist/{1}/setlists?p={0}".format(p, mbid), headers=headers)
            try:
                response = loads(r.text)
            except decoder.JSONDecodeError:
                response = {}
            if "setlist" in response:
                for concert in response["setlist"]:
                    events.append(self.map_platform_to_schema(concert, band, mbid, {}))
                total_hits = int(response["total"])
                retrieved_hits += int(response["itemsPerPage"])
            else:
                total_hits = 0
            p += 1

        if events:
            for concert in events:
                if isinstance(concert, dict):
                    print("setlist", concert)
                    concertannouncement = ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first()
                    if not concertannouncement:
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
                    else:
                        if concert["titel"] != concertannouncement.title:
                            concertannouncement.title = concert["titel"][0:199]
                        if concert["datum"] != concertannouncement.date:
                            concertannouncement.date = concert["datum"]
                        if concert["latitude"] != concertannouncement.latitude:
                            concertannouncement.latitude = concert["latitude"]
                        if concert["longitude"] != concertannouncement.longitude:
                            concertannouncement.longitude = concert["longitude"]
                        concertannouncement.last_seen_on = datetime.now()
                        concertannouncement.save()

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
            "source": self.platform,
            "event_id": concert["id"]
        }


class SongkickLeecher(PlatformLeecher):
    def __init__(self):
        super().__init__()
        self.gf = GigFinder.objects.filter(name="www.songkick.com").first()
        try:
            with open("hlwtadmin/songkick_api_key.txt", "r") as f:
                self.platform_access_granter = f.read()
        except FileNotFoundError:
            self.platform_access_granter = self.gf.api_key
        self.platform = "www.songkick.com"
        self.past_events_url = "http://api.songkick.com/api/3.0/artists/{0}/gigography.json?apikey={1}&page={2}"
        self.future_events_url = "http://api.songkick.com/api/3.0/artists/{0}/calendar.json?apikey={1}&page={2}"
        print("songkick api", self.platform_access_granter)


    def set_events_for_identifier(self, band, mbid, url):
        artist_id, artist_name = url.split("/")[-1].split("-")[0], " ".join(url.split("/")[-1].split("-")[1:])
        self.get_events(self.past_events_url, artist_id, artist_name, band, mbid)
        self.get_events(self.future_events_url, artist_id, artist_name, band, mbid)

    def get_events(self, base_url, artistid, artistname, band, mbid):
        page = 1
        url = base_url.format(artistid, self.platform_access_granter, page)
        html = get(url).text
        events = []
        try:
            json_response = loads(html) if html is not None else {}
        except decoder.JSONDecodeError:
            json_response = {}
        if "resultsPage" in json_response:
            resultspage = json_response["resultsPage"]
            amount_events = resultspage["totalEntries"] if "totalEntries" in resultspage else 0
            amount_pages = ceil(amount_events / 50.0)
            while page <= amount_pages:
                if resultspage["status"] == "ok":
                    for event in resultspage["results"]["event"]:
                        events.append(self.map_platform_to_schema(event, band, mbid, {"artist_id": artistid, "artist_name": artistname}))
                    page += 1
                    url = base_url.format(artistid, self.platform_access_granter, page)
                    html = get(url).text
                    try:
                        resultspage = loads(html)["resultsPage"]
                    except decoder.JSONDecodeError:
                        print("decoder error")
                        resultspage = {"status": "nok"}

        if events:
            for concert in events:
                if isinstance(concert, dict):
                    print("songkick", concert)
                    concertannouncement = ConcertAnnouncement.objects.filter(gigfinder_concert_id=concert["event_id"]).filter(gigfinder=self.gf).first()
                    if not concertannouncement:
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
                    else:
                        if concert["titel"] != concertannouncement.title:
                            concertannouncement.title = concert["titel"]
                        if concert["datum"] != concertannouncement.date:
                            concertannouncement.date = concert["datum"]
                        if concert["latitude"] != concertannouncement.latitude:
                            concertannouncement.latitude = concert["latitude"]
                        if concert["longitude"] != concertannouncement.longitude:
                            concertannouncement.longitude = concert["longitude"]
                        concertannouncement.last_seen_on = datetime.now()
                        concertannouncement.save()

    def map_platform_to_schema(self, event, band, mbid, other):
        concertdate = dateparse(event["start"]["date"]).date()
        return {
            "titel": event["displayName"].strip().rstrip(concertdate.strftime("%B %d, %Y")),
            "datum": concertdate,
            "artiest": other["artist_name"],
            "artiest_id": str(other["artist_id"]),
            "artiest_mb_naam": band,
            "artiest_mb_id": mbid,
            "stad": ",".join([i.strip() for i in event["location"]["city"].split(",")[0:-1]]),
            "land": event["location"]["city"].split(",")[-1].strip(),
            "venue": event["displayName"].strip() if event["type"] == "Festival" else event["venue"]["displayName"].strip(),
            "latitude": event["venue"]["lat"],
            "longitude": event["venue"]["lng"],
            "source": self.platform,
            "event_id": str(event["id"]),
            "event_type": event["type"].lower()
        }
