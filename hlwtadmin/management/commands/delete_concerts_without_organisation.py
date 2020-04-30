from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(relationconcertorganisation__organisation__isnull=True):
            print(concert, concert.pk)
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert = None
                ca.save()
            for rel in RelationConcertOrganisation.objects.filter(concert=concert):
                rel.delete()
            for rel in RelationConcertArtist.objects.filter(concert=concert):
                rel.delete()
            concert.delete()