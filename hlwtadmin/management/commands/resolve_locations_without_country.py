from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for loc in Location.objects.filter(country__isnull=True):
            print("loc", loc)
            org = Organisation.objects.filter(location=loc).first()
            if org:
                print("org", org)
                venue = Venue.objects.filter(organisation=org).first()
                if venue:
                    print("venue", venue)
                    land = venue.raw_venue.split("|")[-2]
                    stad = venue.raw_venue.split("|")[-3]
                    print("location", stad, land)
                    country = Country.objects.filter(name=land).first()
                    if not country:
                        country = Country.objects.filter(iso_code=land.lower()).first()
                    if country:
                        country = country.replace("Nederland", "nl").replace("België", "be")
                        print("found a country", country)
                        location = Location.objects.filter(country=country).filter(city=stad).first()
                        if location:
                            print("found a location", location)
                            for this_org in Organisation.objects.filter(location=loc):
                                this_org.location = location
                                this_org.save()
                            loc.delete()
                        else:
                            print("adding country to location", country)
                            loc.country = country
                            loc.save()
