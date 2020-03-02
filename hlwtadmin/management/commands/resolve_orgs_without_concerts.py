from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for organisation in Organisation.objects.filter(relationconcertorganisation__organisation__isnull=True).distinct():
            venue = Venue.objects.filter(organisation=organisation).first()
            if venue:
                cas = ConcertAnnouncement.objects.filter(raw_venue=venue)
                for ca in cas:
                    concert = ca.concert
                    if concert:
                        print(organisation, "has as concert", concert)
                        RelationConcertOrganisation.objects.create(
                            concert=concert,
                            organisation=organisation
                        )
