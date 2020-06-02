from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for venue in Venue.objects.exclude(organisation__isnull=True).exclude(organisation__location__country__isnull=True).exclude(non_assignable=True):
            org_loc = venue.organisation.location
            try:
                if venue.concertannouncement_set.first():
                    likely_location = venue.concertannouncement_set.first().clean_location_from_string()
                    if likely_location and likely_location.pk != 34789:
                        if org_loc != likely_location:
                            print("\t".join([venue.raw_venue, str(venue.pk),
                                             venue.organisation.name, str(venue.organisation.id),
                                             str(org_loc.city), str(org_loc.country.name), str(org_loc.pk),
                                             str(likely_location.city), str(likely_location.country.name if likely_location.country else None), str(likely_location.pk)]))
            except Exception as e:
                pass
