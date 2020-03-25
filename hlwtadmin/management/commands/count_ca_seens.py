from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for ca in ConcertAnnouncement.objects.all():
            if ca.last_seen_on != ca.created_at.date():
                ca.save(update_fields=['seen_count'])
                print(ca, ca.seen_count, ca.created_at, ca.last_seen_on)
