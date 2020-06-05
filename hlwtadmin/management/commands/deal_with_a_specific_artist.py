from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(relationconcertartist__artist__mbid="ccc74478-30ee-47de-a8a7-d571607036b5"):
            print("found concert", concert, concert.id)
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                print("found announcement", ca, ca.id)
                ca.concert = None
                ca.delete()

            RelationConcertOrganisation.objects.filter(concert=concert).all().delete()
            RelationConcertArtist.objects.filter(concert=concert).all().delete()
            concert.delete()

        for venue in Venue.objects.filter(concertannouncement__isnull=True):
            print("found a orphaned venue", venue, venue.id)
            venue.organisation = None
            venue.delete()

        for organisation in Organisation.objects.filter(relationconcertorganisation__isnull=True).filter(venue__isnull=True):
            print("found a orphaned organisation", organisation, organisation.id)
            input()
            organisation.delete()

        for location in Location.objects.exclude(verified=True).filter(organisation__isnull=True):
            print("found a orphaned location", location, location.id)
            input()
            location.delete()
