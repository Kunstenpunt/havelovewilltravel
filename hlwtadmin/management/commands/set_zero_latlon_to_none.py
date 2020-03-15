from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for obj in Organisation.objects.filter(latitude__isnull=True):
            print(obj, obj.latitude, obj.longitude)
            obj.latitude = None
            obj.longitude = None
            obj.save()

        for obj in Concert.objects.filter(latitude__isnull=True):
            print(obj, obj.latitude, obj.longitude)
            obj.latitude = None
            obj.longitude = None
            obj.save()

        for obj in Location.objects.filter(latitude__isnull=True):
            print(obj, obj.latitude, obj.longitude)
            obj.latitude = None
            obj.longitude = None
            obj.save()

        for obj in ConcertAnnouncement.objects.filter(latitude__isnull=True):
            print(obj, obj.latitude, obj.longitude)
            obj.latitude = None
            obj.longitude = None
            obj.save()
