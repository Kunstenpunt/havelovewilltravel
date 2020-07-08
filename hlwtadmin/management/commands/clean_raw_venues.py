from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        done = []
        i = 1
        for raw_venue in Venue.objects.all():
            if raw_venue.pk not in done:
                try:
                    for dup_venue in Venue.objects.filter(raw_venue=raw_venue.raw_venue).exclude(organisation=raw_venue.organisation).exclude(pk=raw_venue.pk):
                        print(i, "http://hlwtadmin.herokuapp.com/hlwtadmin/venue/" + str(raw_venue.pk), str(raw_venue).encode('utf-8'), "is similar to", "http://hlwtadmin.herokuapp.com/hlwtadmin/venue/" + str(dup_venue.pk), str(dup_venue).encode('utf-8'))
                        done.append(dup_venue.pk)
                        i += 1
                except Exception as e:
                    pass

