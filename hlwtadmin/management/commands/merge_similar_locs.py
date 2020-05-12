from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for loc in Location.objects.filter(verified=True):
            loccity = loc.city
            loccity = loccity.replace("-", ".").replace("é", "[eé]").replace("è", "[eè]")
            print("searching similar locs for", loc, loc.id)
            mergelocs = []
            for simloc in Location.objects.exclude(verified=True).filter(country=loc.country).filter(city__iregex="^" + loccity + "$"):
                print("\tThe given location is very similar to", simloc, simloc.id)
                mergelocs.append(simloc)

            if len(mergelocs) > 0:
                loc_merge = LocationsMerge.objects.create(
                    primary_object=loc
                )
                loc_merge.alias_objects.set(mergelocs)
                loc_merge.delete()
                input()
