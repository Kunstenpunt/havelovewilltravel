from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError

from pandas import read_excel
from json import load, dump
from codecs import open

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        locs = read_excel("hlwtadmin/management/commands/hlwtadmin_locations.xlsx")
        cl = locs.to_dict('index')

        with open("hlwtadmin/management/commands/cl.json", "w", "utf-8") as f:
            cl = dump(cl, f)

        for organisation in Organisation.objects.filter(location__isnull=True):
            venue = Venue.objects.filter(organisation=organisation).first()
            if venue:
                print(venue)
                org, stad, land, bron, *rest = venue.raw_venue.split("|")
                print("trying with", stad, land)
                if venue.raw_location in cl:
                    stad = cl[venue.raw_location]["clean city"]
                    land = cl[venue.raw_location]["clean country"]
                    print("wait a second, found something better", stad, land)

                    print("hunting a location for", stad, land)
                    country = Country.objects.filter(name=land).first()
                    if not country:
                        country = Country.objects.filter(iso_code=land.lower()).first()
                    if country:
                        print("found a country", country)
                        location = Location.objects.filter(country=country).filter(city=stad).first()
                        if location:
                            print("found a location", location)
                        else:
                            print("creating a location with country", country)
                            location = Location.objects.create(city=stad, country=country, verified=False)
                    else:
                        print("did not find anything")
                        location = Location.objects.create(city=stad + ", " + land, verified=False)
                    organisation.location = location
                    organisation.save()
                    print("linked", location, "to", organisation)
