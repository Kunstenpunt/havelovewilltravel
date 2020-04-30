from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.annotate(num_ca=Count('concertannouncement')).filter(num_ca=0):
            print(concert.id, concert, concert.date)
            RelationConcertOrganisation.objects.filter(concert=concert).delete()
            RelationConcertArtist.objects.filter(concert=concert).delete()
            RelationConcertConcert.objects.filter(concert_a=concert).delete()
            RelationConcertConcert.objects.filter(concert_b=concert).delete()
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert = None
                ca.save()
            concert.delete()
