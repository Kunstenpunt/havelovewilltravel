from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertannouncementToConcert

from django.core.management.base import BaseCommand, CommandError

from datetime import datetime

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True):
        #for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True).filter(raw_venue__organisation__location__pk=34789):
            print("concertannouncement\thttp://hlwtadmin.herokuapp.com/hlwtadmin/concertannouncement/" + str(concertannouncement.pk) + "\trelated venue\thttp://hlwtadmin.herokuapp.com/hlwtadmin/venue/" + str(concertannouncement.raw_venue.pk) if concertannouncement.raw_venue else "---")
            ca2c = ConcertannouncementToConcert(concertannouncement)
            ca2c.automate()
            concertannouncement.save()
