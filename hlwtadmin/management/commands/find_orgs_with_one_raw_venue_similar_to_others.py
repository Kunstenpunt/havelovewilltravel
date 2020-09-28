from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from pandas import read_excel
from django.db.models import Count

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        i = 1
        for org in Organisation.objects.annotate(num_venues=Count('venue')).filter(num_venues=1).filter(venue__concertannouncement__gigfinder__name__icontains="songkick").order_by('pk'):
            for sim_org in Organisation.objects.filter(name__iexact=org.name).exclude(pk=org.pk).filter(location__country=org.location.country).order_by('pk').filter(pk__gt=org.pk):
                line = [str(i), org.name, str(org.pk), str(org.location), "<", sim_org.name, str(sim_org.pk), str(sim_org.location)]
                print("\t".join(line))
                i += 1
