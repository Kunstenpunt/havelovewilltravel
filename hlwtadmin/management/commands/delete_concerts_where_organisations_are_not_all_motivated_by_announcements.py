from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError
from codecs import open

from django.db.models import Q, Exists, Count, F, Max, DateField


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.annotate(num_countries=Count('relationconcertorganisation__organisation__location', distinct=True)).filter(num_countries__gte=2):
            if concert.is_ontologically_sound() == False:
                for ca in ConcertAnnouncement.objects.filter(concert=concert):
                    ca.concert = None
                    ca.save(update_fields=['concert'])
                for rel in RelationConcertOrganisation.objects.filter(concert=concert):
                    rel.delete()
                for rel in RelationConcertArtist.objects.filter(concert=concert):
                    rel.delete()
                concert.delete()
