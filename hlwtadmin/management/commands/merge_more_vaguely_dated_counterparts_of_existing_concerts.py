from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from collections import Counter

from django.db.models import Prefetch
from django_super_deduper.merge import MergedModelInstance


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # get concerts from all organisations with vague dates
        concerts = Concert.objects.filter(until_date__isnull=False)
        for concert in concerts:
            print("looking for specific concert for", concert, concert.until_date)
            similar_concerts = Concert.objects.filter(relationconcertartist__artist__in=[rel.artist for rel in concert.artistsqs()]).filter(relationconcertorganisation__organisation__in=[rel.organisation for rel in concert.organisationsqs()]).filter(until_date__isnull=True).filter(date__gte=concert.date).filter(date__lte=concert.until_date)
            for similar_concert in similar_concerts:
                print("\tsimilar", similar_concert)
            input()

