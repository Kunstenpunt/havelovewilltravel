from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for organisation in Organisation.objects.filter(location__isnull=True):
            venue = Venue.objects.filter(organisation=organisation).first()
            if venue:
                print(venue)
                org, stad, land, bron, *rest = venue.raw_venue.split("|")
                print("location", stad, land)
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
