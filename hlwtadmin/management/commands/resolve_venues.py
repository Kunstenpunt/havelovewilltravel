from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country

from django.core.management.base import BaseCommand, CommandError
from json import load
from codecs import open


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        location_pk = {}
        country_pk = {}

        locations = Location.objects.all()
        for loc in locations:
            city = loc.city
            state = loc.subcountry
            country = loc.country.name if loc.country else None
            location_pk[(city, country)] = loc.id
            country_pk[country] = loc.country.id if loc.country else None

        venues_without_org = Venue.objects.filter(organisation__isnull=True).filter(non_assignable=False)
        for venue in venues_without_org:
            try:
                name_prop, stad, land, bron, *rest = venue.raw_venue.split("|")
                print(name_prop, stad, land)
                ca = ConcertAnnouncement.objects.filter(raw_venue=venue).first()
                lat = ca.latitude
                lon = ca.longitude

                with open("hlwtadmin/management/commands/clocs.json", "r", "utf-8") as f:
                    cl = load(f)

                print("trying to find a better match with", venue.raw_location, venue.raw_location in cl)
                if venue.raw_location in cl:
                    stad = cl[venue.raw_location]["clean city"]
                    land = cl[venue.raw_location]["clean country"]
                    print("wait a found something better", stad, land)

                try:
                    loc = Location.objects.filter(id=location_pk[(stad, land)]).first()
                    print("found loc", loc)
                except KeyError:
                    try:
                        country = Country.objects.filter(id=country_pk[land]).first()
                    except KeyError:
                        country = None
                    loc = Location.objects.create(
                        verified=False,
                        city=stad,
                        country=country
                    )
                    loc.save()
                    location_pk[(stad, land)] = loc.id
                    print("created loc", loc)

                try:
                    org = Organisation.objects.filter(name=name_prop).filter(location__pk=loc.pk).first()
                    print("checking for org", name_prop ,"with location", loc, "and found", org)
                    if org is None:
                        org = Organisation.objects.filter(name=name_prop).filter(location__isnull=True).first()
                        print("checking for an org without location, and found", org)
                        org.location = loc
                        print("added", loc, "to", org)
                except (KeyError, AttributeError):
                    print("no org found, making one")
                    org = Organisation.objects.create(
                        location=loc,
                        verified=False,
                        latitude=lat,
                        longitude=lon,
                        name=name_prop
                    )
                    org.save()
                    print("created org", org, org.location)

                venue.organisation = org
                venue.save()
                print("venue is now", venue, venue.organisation)
            except ValueError:
                pass
