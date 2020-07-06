from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        done = []
        for rel in RelationConcertArtist.objects.all():
            if rel.pk not in done:
                concert = rel.concert
                artist = rel.artist
                concurring = []
                for concur in RelationConcertArtist.objects.filter(concert__date=concert.date).filter(artist=artist).exclude(pk=rel.pk):
                    if concur.pk not in done:
                        concurring.append("\ttogether with http://hlwtadmin.herokuapp.com/concert/" + str(concur.concert.pk) + " " + str(concur.concert.date) + " " + str(concur.concert.organisations()))
                        done.append(concur.pk)
                if len(concurring) > 0:
                    print("http://hlwtadmin.herokuapp.com/concert/" + str(concert.pk), artist, concert.date, concert.organisations())
                    for c in concurring:
                        print(c + "\t(!)" if "None" in c else c)
                done.append(rel.pk)

