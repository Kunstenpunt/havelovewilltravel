from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for rel in RelationConcertOrganisation.objects.filter(organisation__name__icontains="unknown"):
            for rel2 in rel.concert.organisationsqs():
                if "unknown" not in rel2.organisation.name.lower():
                    print(rel.concert, rel.concert.pk)
                    try:
                        rel.delete()
                    except AssertionError:
                        pass
