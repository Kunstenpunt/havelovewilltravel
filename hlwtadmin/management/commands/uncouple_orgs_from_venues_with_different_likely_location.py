from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for venue in Venue.objects.exclude(organisation__isnull=True).exclude(organisation__location__country__isnull=True).exclude(non_assignable=True):
            print(venue, venue.pk)
            org_loc = venue.organisation.location
            likely_location = venue.concertannouncement_set.first().clean_location_from_string()
            if likely_location and likely_location.pk != 34789:
                print(org_loc, likely_location, org_loc == likely_location)
                if org_loc != likely_location:
                    print(org_loc.pk, org_loc, likely_location, likely_location.pk)
                    venue.organisation = None
                    venue.save(update_fields=["organisation"])
