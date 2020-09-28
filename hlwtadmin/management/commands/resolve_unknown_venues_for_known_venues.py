from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, Location

from django.core.management.base import BaseCommand, CommandError

from pandas import read_excel
from json import load, dump
from codecs import open

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        i = 1
        for organisation in Organisation.objects.filter(name__icontains="unknown"):
            for rel in RelationConcertOrganisation.objects.filter(organisation=organisation):
                concert = rel.concert
                for ca in concert.concertannouncements():
                    if "songkick" in ca.gigfinder.name and ca.is_festival:
                        raw_venue = ca.raw_venue
                        venue_organisation = raw_venue.organisation
                        if venue_organisation and "unknown" not in venue_organisation.name.lower():
                            line = [str(i), "concert", str(concert), str(concert.pk), "with organisation", str(organisation), str(organisation.pk), "has ca", str(ca), str(ca.pk), "with raw venue", str(raw_venue), str(raw_venue.pk), "which has organisation", str(venue_organisation), str(venue_organisation.pk) if venue_organisation else str(None)]
                            print("\t".join(line))
                            i += 1
                            rel.organisation = venue_organisation
                            rel.save()
