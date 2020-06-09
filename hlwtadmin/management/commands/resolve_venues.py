from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country

from django.core.management.base import BaseCommand, CommandError
from json import load
from codecs import open
from collections import Counter
from re import sub


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        cl_temp = {}
        for venue in Venue.objects.exclude(organisation__isnull=True):
            key = venue.raw_location
            clean_loc = venue.organisation.location
            clean_city = clean_loc.city
            clean_country = clean_loc.country.name if clean_loc.country else None
            if key not in cl_temp:
                cl_temp[key] = []
            cl_temp[key].append((clean_city, clean_country))

        cl = {}
        for key in cl_temp:
            hit = Counter(cl_temp[key]).most_common(1)[0][0]
            cl[key] = {"clean_city": hit[0], "clean_country": hit[1]}

        print(cl)

        location_pk = {}
        country_pk = {}

        locations = Location.objects.all()
        for loc in locations:
            city = loc.city
            state = loc.subcountry
            country = loc.country.name if loc.country else None
            location_pk[(city, country)] = loc.id
            country_pk[country] = loc.country.id if loc.country else None

        venues_without_org = Venue.objects.exclude(raw_venue__icontains="|none|none|").exclude(raw_venue__icontains="||").exclude(raw_venue__istartswith="unknown").filter(organisation__isnull=True).filter(non_assignable=False)#.filter(pk__gt=100000)
        for venue in venues_without_org:
            try:
                name_prop, stad, land, bron, *rest = venue.raw_venue.split("|")
                print(name_prop, stad, land)
                ca = ConcertAnnouncement.objects.filter(raw_venue=venue).first()
                lat = ca.latitude
                lon = ca.longitude

                print("trying to find a better match with", venue.raw_location, venue.raw_location in cl)
                if venue.raw_location in cl:
                    stad = cl[venue.raw_location]["clean_city"]
                    land = cl[venue.raw_location]["clean_country"]
                    print("wait a found something better", stad, land)

                try:
                    loc = Location.objects.filter(id=location_pk[(stad, land)]).first()
                    print("found loc", loc)
                except KeyError:
                    # try:
                    #     country = Country.objects.filter(id=country_pk[land]).first()
                    # except KeyError:
                    #     country = None
                    # loc = Location.objects.create(
                    #     verified=False,
                    #     city=stad,
                    #     country=country
                    # )
                    # loc.save()
                    # location_pk[(stad, land)] = loc.id
                    # print("created loc", loc)
                    loc = None
                    print("no loc found")

                if loc:
                    try:
                        name_prop_clean = sub("\d\d\d\d$", "", name_prop).strip()
                        print("original name", name_prop, "so cleaned this would be", name_prop_clean)
                        org = Organisation.objects.filter(name=name_prop_clean).filter(location__pk=loc.pk).first()
                        print("checking for org", name_prop_clean, "with location", loc, "and found", org)
                    except (KeyError, AttributeError):
                        org = None

                    if org is None:
                        print("no org found, making one")
                        org = Organisation.objects.create(
                            location=loc,
                            verified=False,
                            latitude=lat,
                            longitude=lon,
                            name=name_prop_clean
                        )
                        print("about to save", org)
                        org.save()
                        print("created org", org, org.location)

                    print("about to connect", venue, "with", org)
                    venue.organisation = org
                    venue.save()
                    print("venue is now", venue, venue.organisation)

            except (KeyError, ValueError):
                pass
