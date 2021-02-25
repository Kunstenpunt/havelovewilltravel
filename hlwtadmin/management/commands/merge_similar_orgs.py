from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, OrganisationsMerge, RelationLocationLocation

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        for org in Organisation.objects.all():
            if org.name != org.name.strip():
                org.name = org.name.strip()
                org.save(update_fields=['name'])

        mapper = {
            "Ã¼": "ü",
            "Ã¨": "è",
            "ÃŸ": "ß",
            "Ã´": "ô",
            "Ã©": "é",
            "Ã¶": "ö",
            "Ã‰": "É",
            "Ãº": "ú",
            "Ã¢": "â",
            "ĂŠ": "é"
        }

        # for rel in RelationLocationLocation.objects.all():
        #     loc = Location.objects.get(pk=rel.location_a.pk)
        #     superloc = Location.objects.get(pk=rel.location_b.pk)
        #     print(loc, "part of", superloc)
        for loc in Location.objects.all():
            for org in Organisation.objects.filter(location=loc).order_by('disambiguation'):
                for map in mapper:
                    new_name = str(org.name).replace(map, mapper[map]).strip()
                    if new_name != org.name:
                        org.name = new_name
                        org.save(update_fields=['name'])
                mergeorgs = []
                #for simorg in Organisation.objects.filter(location=superloc).filter(name__unaccent__iexact=org.name).exclude(pk=org.pk):
                for simorg in Organisation.objects.filter(location=loc).filter(name__unaccent__iexact=org.name).exclude(pk=org.pk):
                    print("\t", org, org.id, "is very similar to", simorg, simorg.id)
                    mergeorgs.append(simorg)

                if len(mergeorgs) > 0:
                    try:
                        org_merge = OrganisationsMerge.objects.create(
                            primary_object=org
                        )
                        org_merge.alias_objects.set(mergeorgs)
                        org_merge.delete()
                        print("\tdone!")
                    except Exception as e:
                        print("\texception", e)
                        pass
