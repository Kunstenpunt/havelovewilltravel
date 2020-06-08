from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.annotate(num_ca=Count('concertannouncement')).filter(num_ca=1).exclude(concertannouncement__until_date__isnull=True).filter(until_date__isnull=True):
            print(concert.pk, concert)
            concert.until_date = concert.concertannouncement_set.first().until_date
            concert.save(update_fields=['until_date'])

        for concert in Concert.objects.annotate(num_ca=Count('concertannouncement')).filter(num_ca__gt=1).order_by('date'):
            precise_date = set()
            for ca in concert.concertannouncements():
                if ca.until_date is None:
                    precise_date.add(ca.date)
            if len(precise_date) == 1:
                print(concert.pk, concert, "with multiple announcements, and at least one is precise")
                if concert.until_date is not None or concert.date != list(precise_date)[0]:
                    print("\tadjusting date and until date")
                    concert.until_date = None
                    concert.date = list(precise_date)[0]
                    concert.save(update_fields=['until_date', 'date'])
                for ca in concert.concertannouncements():
                    if ca.until_date is not None:
                        print("\tremoving a vague announcement from this concert")
                        ca.concert = None
                        ca.save(update_fields=['concert'])
            elif len(precise_date) > 1:
                print(concert.pk, concert, "with multiple announcements, and several are precise with different dates")
                print("\tremoving these announcement from this concert")
                input()
                for ca in concert.concertannouncements():
                    ca.concert = None
                    ca.save(update_fields=['concert'])
