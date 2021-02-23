from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertsMerge

from django.core.management.base import BaseCommand, CommandError

from re import escape

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(until_date__isnull=True).order_by('-verified'):
            orgs = [rel.organisation for rel in concert.organisationsqs()]
            arts = [rel.artist for rel in concert.artistsqs()]
            print(concert, concert.date, orgs, arts, concert.pk)
            mergeconcerts = []
            if len(arts) == 1:
                artist = arts[0]
                art_concerts = [rel.concert for rel in RelationConcertArtist.objects.filter(artist=artist).filter(concert__date=concert.date).filter(concert__until_date__isnull=True)]
                for art_concert in art_concerts:
                    if art_concert != concert:
                        if concert.date == art_concert.date:
                            art_orgs = [rel.organisation for rel in art_concert.organisationsqs()]
                            if art_orgs == orgs:
                                print("\t", concert, concert.pk, "is very similar to", art_concert, art_concert.pk)
                                mergeconcerts.append(art_concert)

            if len(mergeconcerts) > 0:
                print("\tlet's do this")
                input()
                try:
                    concert_merge = ConcertsMerge.objects.create(
                        primary_object=concert
                    )
                    concert_merge.alias_objects.set(mergeconcerts)
                    print(concert_merge)
                    concert_merge.merge()
                    print("\tdone")
                    concert_merge.delete()
                except Exception as e:
                    print("\texception", e)
                    pass
