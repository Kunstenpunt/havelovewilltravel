from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(relationconcertorganisation__organisation__isnull=True):
            print(concert, concert.pk)
            ca = ConcertAnnouncement.objects.filter(concert=concert).first()
            if ca:
                venue = ca.raw_venue
                print(venue)
                organisation = venue.organisation
                print(organisation)
                if organisation:
                    print("about to link", organisation, "to", concert)
                    input()
                    rel = RelationConcertOrganisation.objects.create(concert=concert, organisation=organisation)
                    rel.save()
                else:
                    print("no organisation to link")
