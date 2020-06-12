from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        artists = [
            "362698b9-05bd-42d7-ac33-b8fb50cfde7f",
            "eccde7bf-f21c-4b0a-9a83-155273053b98",
            "04a2d286-a0b7-40fe-a909-d6cf8c93c4a7",
            "9dd8a047-7577-4909-917e-08d5e513cc8b",
            "4924967f-6985-4da6-9310-1126f1a9a0c1",
            "2a573763-2f24-4093-91c9-3e0ecf318c50",
            "c8d9ff35-6924-4911-b97a-f0d8e128796a",
            "7596023f-103d-4fb8-b6fe-683bb44577d9",
            "91ff6da8-3a0d-449f-b281-487dc9bd4a9f"
        ]
        for artist in artists:
            for concert in Concert.objects.filter(relationconcertartist__artist__mbid=artist):
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
                organisation.delete()

            for location in Location.objects.exclude(verified=True).filter(organisation__isnull=True):
                print("found a orphaned location", location, location.id)
                location.delete()
