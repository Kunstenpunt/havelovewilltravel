from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        repmap = [
            ", Nederland",
            ", UK",
            ", België",
            ", Duitsland",
            ", CZ",
            ", RU",
            ", HR"
        ]

        for loc in Location.objects.exclude(country__isnull=True).filter(city__contains=', '):
            city = loc.city
            print(city)
            city_new = city
            for rep in repmap:
                city_new = city_new.replace(rep, "")
            if city_new != city:
                print("changing", city, "for", city_new)
                input()
                loc.city = city_new
                loc.save()
