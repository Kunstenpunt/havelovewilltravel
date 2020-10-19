from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(date__gte=datetime(2020,3,13)).filter(date__lte=datetime(2020,6,30)):
            print(concert)
            for ca in concert.concertannouncements():
                print("\t", ca)
                ca.delete()
            concert.delete()
