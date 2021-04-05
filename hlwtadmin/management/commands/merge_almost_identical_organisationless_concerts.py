from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, ConcertsMerge

from django.core.management.base import BaseCommand, CommandError

from re import escape

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(until_date__isnull=True).filter(relationconcertorganisation__organisation__isnull=True).exclude(ignore=True).exclude(cancelled=True):
            arts = [rel.artist for rel in concert.artistsqs()]
            print(concert, concert.date, arts, concert.pk)
            mergeconcerts = None
            if len(arts) == 1:
                artist = arts[0]
                art_concerts = [rel.concert for rel in RelationConcertArtist.objects.filter(artist=artist).filter(concert__date=concert.date).filter(concert__until_date__isnull=True)]
                for art_concert in art_concerts:
                    if art_concert != concert:
                        if concert.date == art_concert.date:
                            if len(art_concert.organisationsqs()) > 0:
                                print("\t", concert, concert.pk, "is very similar to", art_concert, art_concert.pk)
                                mergeconcerts = art_concert

            if mergeconcerts:
                print("\tlet's do this?")
                input()
                try:
                    concert_merge = ConcertsMerge.objects.create(
                        primary_object=mergeconcerts
                    )
                    concert_merge.alias_objects.set([concert])
                    print(concert_merge)
                    input()
                    concert_merge.merge()
                    print("\tdone")
                    concert_merge.delete()
                except Exception as e:
                    print("\texception", e)
                    pass
