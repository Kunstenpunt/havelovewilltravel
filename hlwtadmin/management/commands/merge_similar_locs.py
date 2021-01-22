from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from re import escape

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for loc in Location.objects.order_by('-verified', 'country', '-subcountry'):
            print(loc.city, loc.country, loc.verified)
            loccity = loc.city
            loccity = loccity.replace("-", ".").replace("é", "[eé]").replace("è", "[eè]")
            print("searching similar locs for", loc, loc.id)
            mergelocs = []
            for simloc in Location.objects.filter(country=loc.country).filter(city__unaccent__iregex="^" + escape(loccity) + "$"):
                if simloc != loc and (simloc.subcountry == loc.subcountry or simloc.subcountry is None) and (simloc.zipcode == loc.zipcode or simloc.zipcode is None):
                    print("\tThe given location is very similar to", simloc, simloc.id)
                    mergelocs.append(simloc)

            if len(mergelocs) > 0:
                try:
                    loc_merge = LocationsMerge.objects.create(
                        primary_object=loc
                    )
                    loc_merge.alias_objects.set(mergelocs)
                    input()
                    loc_merge.delete()
                except Exception as e:
                    pass
