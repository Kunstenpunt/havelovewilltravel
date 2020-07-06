from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, OrganisationsMerge

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for loc in Location.objects.all():
            for org in Organisation.objects.filter(location=loc).order_by('disambiguation'):
                print("looking for similar orgs to", org, org.pk, org.disambiguation, "in", loc)
                mergeorgs = []
                for simorg in Organisation.objects.filter(location=loc).filter(name__iexact=org.name).exclude(pk=org.pk):
                    print("\tThe given organisation is very similar to", simorg, simorg.id)
                    mergeorgs.append(simorg)

                if len(mergeorgs) > 0:
                    try:
                        org_merge = OrganisationsMerge.objects.create(
                            primary_object=org
                        )
                        org_merge.alias_objects.set(mergeorgs)
                        org_merge.delete()
                        print("done!")
                    except Exception as e:
                        print("exception", e)
                        pass
