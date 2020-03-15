from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(genre__isnull=True):
            print(org, org.genre.all())
            rels = RelationConcertOrganisation.objects.filter(organisation=org)
            for rel in rels:
                for genre in rel.concert.genre.all():
                    print("concert genre", genre)
                    org.genre.add(genre)
            print(">>>", org, org.genre.all())
