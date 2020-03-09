from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for loc in Location.objects.filter(country__isnull=True):
            print("loc", loc)
            try:
                org = Organisation.objects.filter(location=loc).first()
                if org:
                    print("org", org)
                    venue = Venue.objects.filter(organisation=org)[1]
                    if venue:
                        print("venue", venue)
                        land = venue.raw_venue.split("|")[-2]
                        stad = venue.raw_venue.split("|")[-3]
                        land = land.replace("The Netherlands", "nl").replace("Nederland", "nl").replace("België", "be").replace("UK", "gb").replace("Roemenië", "ro").replace("Frankrijk", "fr").replace("Russian Federation", "ru").replace("Uk", "gb").replace("Duitsland", "de").replace("United States of America", "us").replace("Tsjechië", "cz").replace("Oostenrijk", "at").replace("Korea, Republic Of", "kr")
                        print("location", stad, land)
                        country = Country.objects.filter(name__iexact=land).first()
                        if not country:
                            print("no country found, trying iso code")
                            country = Country.objects.filter(iso_code=land.lower()).first()
                            print("und", country)
                        if country:
                            print("found a country", country)
                            location = Location.objects.filter(country=country).filter(city__iexact=stad).first()
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
                else:
                    loc.delete()
            except IndexError:
                pass