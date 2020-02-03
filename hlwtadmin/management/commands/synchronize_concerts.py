from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue

from musicbrainzngs import set_useragent, search_artists, musicbrainz, get_artist_by_id
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from time import sleep


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def __search_artists_in_area(self, area, limit, offset):
        artists = {"artist-list": [], "artist-count": -1}
        while artists["artist-count"] < 0:
            try:
                sleep(1.0)
                artists_area = search_artists(area=area, beginarea=area, endarea=area, limit=limit, offset=offset)
                artists['artist-list'] = artists_area["artist-list"]
                artists['artist-count'] = artists_area["artist-count"]
            except musicbrainz.NetworkError:
                sleep(25.0)
            except musicbrainz.ResponseError:
                sleep(25.0)
        return artists

    def __create_or_update_artist(self, artist, include=False):
        a = Artist.objects.filter(pk=artist["id"]).first()
        if not a:
            a = Artist.objects.create(name=artist["name"],
                                 disambiguation=artist["disambiguation"] if "disambiguation" in artist else None,
                                 mbid=artist["id"],
                                 include=include,
                                 exclude=False
                                )
        else:
            a.name = artist["name"]
            a.disambiguation = artist["disambiguation"]
            a.include = include
        a.save()

    def __create_or_update_artist_gigfinders(self, artist):
        artistobject = Artist.objects.filter(pk=artist["id"]).first()
        urlrels = artist["url-relation-list"]
        for urlrel in urlrels:
            url = urlrel["target"]
            gigfindername = url.split("/")[2]
            if gigfindername in ["bandsintown.com", "www.songkick.com", "www.setlist.fm", "www.facebook.com"]:
                gf = GigFinder.objects.filter(name=gigfindername).first()
                if not gf:
                    gf = GigFinder.objects.create(name=gigfindername)
                    gf.save()
                gfurl = GigFinderUrl.objects.create(
                    artist=artistobject,
                    gigfinder=gf,
                    url=url
                )
                gfurl.save()

    def __obtain_a_specific_mb_artist(self, mbid):
        set_useragent("kunstenpunt", "0.1", "github.com/kunstenpunt")
        artist = None
        while artist is None:
            try:
                sleep(1.0)
                artist = get_artist_by_id(mbid, includes=["url-rels"])["artist"]
            except musicbrainz.NetworkError as e:
                print("musicbrainz netwerkerror", e)
                sleep(25.0)
            except musicbrainz.Response:
                sleep(25.0)
        return artist

    def handle(self, *args, **options):
        set_useragent("kunstenpunt", "0.1", "github.com/kunstenpunt")
        leecher = FacebookScraper()
        for gfurl in GigFinderUrl.objects.all():
            print(gfurl.artist, gfurl.artist.mbid, gfurl.url, gfurl.gigfinder.name)
            if gfurl.gigfinder.name == "www.facebook.com":
                leecher.set_events_for_identifier(gfurl.artist, gfurl.artist.mbid, gfurl.url)


from json import decoder, loads, dumps
from dateparser import parse as dateparse
from time import sleep
from requests import get
from fake_useragent import UserAgent
from re import compile
from codecs import open
from bs4 import BeautifulSoup


class FacebookScraper(object):
    def __init__(self):
        self.platform = "facebook"
        self.gf = GigFinder.objects.filter(name="www.facebook.com").first()
        self.ua = UserAgent()
        with open("hlwtadmin/google_api_places_api_key.txt", "r") as f:
            self.google_places_api_key = f.read().strip()

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
            print(ld)
            datum = dateparse(ld["startDate"]).date()
            location = self._get_location(ld)
            titel = ld["name"]
            event_data = {
                "event_id": event_id,
                "datum": datum,
                "land": location["country"][0],
                "stad": location["city"][0],
                "venue": location["venue"],
                "latitude": location["lat"],
                "longitude": location["lng"],
                "titel": titel
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
        loc_info["venue"] = location_name
        loc_info["city"] = location_street,
        loc_info["country"] = location_country,
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
                            venue_name = "|".join([concert["venue"], concert["stad"], concert["land"], "facebook"])
                            venue = Venue.objects.filter(raw_venue=venue_name).first()
                            if not venue:
                                venue = Venue.objects.create(
                                    raw_venue=venue_name,
                                    raw_location="|".join([concert["stad"], concert["land"], "facebook"])
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
                                ignore=False
                            )
                            ca.save()

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
