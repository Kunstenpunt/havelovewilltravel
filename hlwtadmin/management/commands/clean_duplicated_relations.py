from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from collections import Counter


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # Delete relations with empty organisations
        RelationConcertOrganisation.objects.filter(organisation__isnull=True).delete()

        # Delete relations with empty artists
        RelationConcertArtist.objects.filter(artist__isnull=True).delete()

        # Clean Concert <> Organisation
        values = RelationConcertOrganisation.objects.all().values_list('concert', 'organisation', 'organisation_credited_as', 'relation_type', 'verified')
        for item, c in Counter(values).most_common():
            if c > 1:
                hit = RelationConcertOrganisation.objects.filter(concert=item[0]).filter(organisation=item[1]).filter(organisation_credited_as=item[2]).filter(relation_type=item[3]).filter(verified=item[4]).first().delete()

        # Same for Concert Artis
        values = RelationConcertArtist.objects.all().values_list('concert', 'artist', 'artist_credited_as', 'relation_type')
        for item, c in Counter(values).most_common():
            if c > 1:
                hit = RelationConcertArtist.objects.filter(concert=item[0]).filter(artist=item[1]).filter(artist_credited_as=item[2]).filter(relation_type=item[3]).first().delete()
