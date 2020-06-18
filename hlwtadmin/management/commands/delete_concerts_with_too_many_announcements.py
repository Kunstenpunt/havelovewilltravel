from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(ignore=True).annotate(num_ca=Count('concertannouncement')).filter(num_ca=1):
            print(concert.id, concert, concert.date)
            input("go for delete?")
            RelationConcertOrganisation.objects.filter(concert=concert).delete()
            RelationConcertArtist.objects.filter(concert=concert).delete()
            RelationConcertConcert.objects.filter(concert_a=concert).delete()
            RelationConcertConcert.objects.filter(concert_b=concert).delete()
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert = None
                ca.ignore = True
                ca.save(update_fields=['concert', 'ignore'])
            concert.delete()
