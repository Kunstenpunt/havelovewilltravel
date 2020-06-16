from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertannouncementToConcert

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True):
            ca2c = ConcertannouncementToConcert(concertannouncement)
            ca2c.automate()
