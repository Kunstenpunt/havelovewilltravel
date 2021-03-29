from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertsMerge

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from collections import Counter

from django.db.models import Prefetch
from django_super_deduper.merge import MergedModelInstance


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # get concerts from all organisations with vague dates
        concerts = Concert.objects.filter(until_date__isnull=False)
        for concert in concerts:
            print("looking for specific concert for", concert.pk, concert, concert.until_date)
            similar_concerts = Concert.objects.filter(relationconcertartist__artist__in=[rel.artist for rel in concert.artistsqs()]).filter(relationconcertorganisation__organisation__location__in=[rel.organisation.location for rel in concert.organisationsqs()]).filter(until_date__isnull=True).filter(date__gte=concert.date).filter(date__lte=concert.until_date)
            if similar_concerts:
                similar_concert = similar_concerts[0]
                print("\tsimilar", similar_concert.pk, similar_concert)

                mergeconcerts = [concert]

                if len(mergeconcerts) > 0:
                    print("\tlet's do this, merge", mergeconcerts, "into", similar_concert)
                    try:
                        concert_merge = ConcertsMerge.objects.create(
                            primary_object=similar_concert
                        )
                        concert_merge.alias_objects.set(mergeconcerts)
                        print(concert_merge)
                        concert_merge.merge()
                        print("\tdone")
                        concert_merge.delete()
                        similar_concert.until_date = None
                        similar_concert.save(update_fields=["until_date"])
                    except Exception as e:
                        print("\texception", e)
                        pass


