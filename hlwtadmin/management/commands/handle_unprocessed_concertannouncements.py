from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertannouncementToConcert

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True).filter(pk__in=(288230, 288306)):
            ca2c = ConcertannouncementToConcert(concertannouncement)
            ca2c.automate()
