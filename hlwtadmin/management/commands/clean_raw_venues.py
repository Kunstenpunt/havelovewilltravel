from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        done = []
        for raw_venue in Venue.objects.all():
            if raw_venue.pk not in done:
                for dup_venue in Venue.objects.filter(raw_venue=raw_venue.raw_venue).exclude(organisation=raw_venue.organisation).exclude(pk=raw_venue.pk):
                    print("http://hlwtadmin.herokuapp.com/hlwtadmin/venue/" + str(raw_venue.pk), raw_venue, "is similar to", "http://hlwtadmin.herokuapp.com/hlwtadmin/venue/" + str(dup_venue.pk), dup_venue)
                    done.append(dup_venue.pk)

