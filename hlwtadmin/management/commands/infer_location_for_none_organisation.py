from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from collections import Counter

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for org in Organisation.objects.filter(location__country__isnull=True):
            print(org, org.location)

            if org.name == "None":
                rels = RelationConcertOrganisation.objects.filter(organisation=org)
                for rel in rels:
                    rel.delete()
                org.delete()

            locs = []
            rels = RelationConcertOrganisation.objects.filter(organisation=org)
            if len(rels) > 0:
                for rel in rels:
                    for rel2 in RelationConcertOrganisation.objects.filter(concert=rel.concert).exclude(organisation=org).exclude(organisation__isnull=True):
                        org2 = rel2.organisation
                        if org2.location != org.location:
                            locs.append(org2.location)
                if len(locs) > 0:
                    new_loc = Counter(locs).most_common(1)[0][0]
                    org.location = new_loc
                    org.save()
                    print(">>>", org, new_loc)
            else:
                org.delete()
