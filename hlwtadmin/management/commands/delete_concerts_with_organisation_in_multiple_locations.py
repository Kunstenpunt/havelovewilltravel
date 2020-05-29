from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.annotate(num_countries=Count('relationconcertorganisation__organisation__location', distinct=True)).filter(num_countries__gte=2):
            print(concert, concert.pk)
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert = None
                ca.save(update_fields=['concert'])
            for rel in RelationConcertOrganisation.objects.filter(concert=concert):
                rel.delete()
            for rel in RelationConcertArtist.objects.filter(concert=concert):
                rel.delete()
            concert.delete()
