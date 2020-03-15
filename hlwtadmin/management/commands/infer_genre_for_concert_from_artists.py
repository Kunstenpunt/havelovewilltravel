from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(genre__isnull=True):
            print(concert, concert.genre.all())
            rels = RelationConcertArtist.objects.filter(concert=concert)
            for rel in rels:
                for genre in rel.artist.genre.all():
                    print("artist genre", genre)
                    concert.genre.add(genre)
            print(">>>", concert, concert.genre.all())
