from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        i = 1
        for raw_venue in Venue.objects.filter(non_assignable=False).filter(raw_location__icontains="||").filter(organisation__location__city="Gent"):
            print(i, raw_venue)
            raw_venue.non_assignable = True
            if "Gent" not in raw_venue.raw_venue:
                print("\tremoving organisation")
                raw_venue.organisation = None
            raw_venue.save()
            i += 1


