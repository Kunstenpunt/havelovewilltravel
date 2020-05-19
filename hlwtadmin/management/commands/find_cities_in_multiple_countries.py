from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from pandas import read_excel


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        previous_loc_id = -1
        for loc in Location.objects.exclude(city__isnull=True).order_by('id'):
            city = loc.city
            for simloc in Location.objects.filter(city=city).exclude(id=loc.id).filter(id__gt=previous_loc_id):
                sim = [str(loc.id), city, loc.country.name if loc.country else 'None', "is similar to", str(simloc.id), simloc.city, simloc.country.name if simloc.country else 'None']
                print("\t".join(sim).encode("utf-8"))
            previous_loc_id = loc.id
