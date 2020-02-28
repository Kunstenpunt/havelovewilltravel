from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(relationconcertorganisation__organisation__isnull=True):
            ca = ConcertAnnouncement.objects.filter(concert=concert).first()
            if ca:
                venue = ca.raw_venue
                print(venue)
                organisation = venue.organisation
                rel = RelationConcertOrganisation.objects.filter(concert=concert).first()
                rel.organisation = organisation
                rel.save()
                print("linked", organisation, "to", concert)
