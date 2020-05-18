from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from pandas import read_excel


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        nl = read_excel("hlwtadmin/management/commands/NL Gemeenten alfabetisch 2020.xlsx", header=0)
        country = Country.objects.filter(name="Netherlands").first()

        for loc in Location.objects.filter(country=country):
            loc.verified=False
            loc.save(update_fields=['verified'])

        for loc in nl.iterrows():
            city = loc[1]["Gemeentenaam"]
            subcountry = loc[1]["Provincienaam"]
            potential_match = Location.objects.filter(country=country).filter(subcountry=subcountry).filter(city=city).first()
            if potential_match:
                potential_match.verified = True
                potential_match.save(update_fields=['verified'])
                print("verified", potential_match)
            else:
                new_loc = Location.objects.create(
                    city=city,
                    subcountry=subcountry,
                    country=country,
                    verified=True
                )
                new_loc.save()
                print("created", new_loc)
