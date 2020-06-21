from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError
from codecs import open

from django.db.models import Q, Exists, Count, F, Max, DateField


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        i = 1
        lines = []
        for venue in Venue.objects.filter(organisation__isnull=False):
            raw_loc = venue.raw_location
            string_based_loc = venue.location_estimated_from_raw_loc_string()
            assignment_loc = venue.location_estimated_from_venues_with_similar_raw_loc()
            organisation_loc = venue.organisation.location
            if organisation_loc != assignment_loc and str(assignment_loc) != "None, No country":
                line = "; ".join([str(i), str(venue.pk), str(venue.raw_venue), str(raw_loc), str(string_based_loc), str(assignment_loc), str(organisation_loc), str(venue.organisation.name), str(venue.organisation.pk)])
                print(line)
                lines.append(line)
                i += 1

        with open("venues_with_locations.csv", "w", "utf-8") as f:
            f.write("\n".join(lines))
