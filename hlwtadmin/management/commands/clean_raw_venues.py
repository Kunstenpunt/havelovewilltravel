from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        done = []
        for raw_venue in Venue.objects.all():
            if raw_venue.pk not in done:
                for dup_venue in Venue.objects.filter(raw_venue=raw_venue.raw_venue).filter(organisation=raw_venue.organisation).exclude(pk=raw_venue.pk):
                    print(raw_venue.pk, raw_venue, "is equal to", dup_venue.pk, dup_venue)
                    for ca in ConcertAnnouncement.objects.filter(raw_venue=dup_venue):
                        print("\tadjusting", ca.pk, ca)
                        ca.raw_venue = raw_venue
                        ca.save(update_fields=['raw_venue'])
                    dup_venue.organisation = None
                    done.append(dup_venue.pk)
                    dup_venue.delete()
