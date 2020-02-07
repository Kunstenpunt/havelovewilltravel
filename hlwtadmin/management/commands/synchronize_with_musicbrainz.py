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
        print(artist)
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
            a.disambiguation = artist["disambiguation"] if "disambiguation" in artist else None
            a.include = include
        a.save()

    def __create_or_update_artist_gigfinders(self, artist):
        print(artist)
        artistobject = Artist.objects.filter(pk=artist["id"]).first()
        urlrels = artist["url-relation-list"] if "url-relation-list" in artist else []
        for urlrel in urlrels:
            url = urlrel["target"]
            gigfindername = url.split("/")[2]
            if gigfindername in ["bandsintown.com", "www.songkick.com", "www.setlist.fm", "www.facebook.com"]:
                gf = GigFinder.objects.filter(name=gigfindername).first()
                if not gf:
                    gf = GigFinder.objects.create(name=gigfindername)
                    gf.save()
                if GigFinderUrl.objects.filter(url=url).filter(artist=artistobject).first() is None:
                    gfurl = GigFinderUrl.objects.create(
                        artist=artistobject,
                        gigfinder=gf,
                        url=url
                    )
                    gfurl.save()

    def handle(self, *args, **options):
        # delete all gigfinder
        GigFinderUrl.objects.all().delete()
        # get new artists or updates from musicbrainz
        updated = []
        set_useragent("kunstenpunt", "0.1", "github.com/kunstenpunt")
        i = 1
        offset = 0
        limit = 25
        total_search_results = 1
        while offset < total_search_results:
            search_results = self.__search_artists_in_area("Eeklo", limit, offset)
            for hit in list(search_results["artist-list"]):
                artist = self.__obtain_a_specific_mb_artist(hit["id"])
                self.__create_or_update_artist(artist)
                self.__create_or_update_artist_gigfinders(artist)
                updated.append(hit["id"])
                i += 1
            offset += limit
            total_search_results = search_results["artist-count"]
        # go through existing artists not found above
        for artistobject in Artist.objects.all():
            if artistobject.mbid not in updated and not artistobject.exclude:
                artist = self.__obtain_a_specific_mb_artist(artistobject.mbid)
                self.__create_or_update_artist(artist, include=True)
                self.__create_or_update_artist_gigfinders(artist)

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
