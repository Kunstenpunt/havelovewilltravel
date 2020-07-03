from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError
from codecs import open

from django.db.models import Q, Exists, Count, F, Max, DateField


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        us_organisations = Organisation.objects.filter(location__country__name="United States")
        for org in us_organisations:
            org_city = org.location.city
            for org_match in us_organisations.filter(name__iexact=org.name).filter(location__city=org_city).exclude(pk=org.pk).exclude(location__subcountry=org.location.subcountry):
                line = [str(org.pk), str(org), str(org.location.city), str(org.location.subcountry), str(org_match.pk), str(org_match), str(org_match.location.city), str(org_match.location.subcountry)]
                print("\t".join(line))
