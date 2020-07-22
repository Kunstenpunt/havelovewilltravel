from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models.functions import Length

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(name__iregex="\w\s\d\d\d\d$"):
            if 1980 < int(org.name[-4:]) < 2030:
                org.name = org.name[:-5].strip()
                org.save(update_fields=['name'])
