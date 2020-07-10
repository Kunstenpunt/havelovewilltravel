from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertannouncementToConcert

from django.core.management.base import BaseCommand, CommandError

from datetime import datetime

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True).filter(date__lt=datetime(2018, 8, 31))[:1000]:
            print("concertannouncement http://hlwtadmin.herokuapp.com/hlwtadmin/concertannouncement/" + str(concertannouncement.pk))
            ca2c = ConcertannouncementToConcert(concertannouncement)
            ca2c.automate()
            concertannouncement.save()
