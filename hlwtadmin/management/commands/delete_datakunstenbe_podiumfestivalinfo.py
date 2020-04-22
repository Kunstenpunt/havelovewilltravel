from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(concertannouncement__gigfinder__name="datakunstenbe"):
            print(concert, concert.pk)
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert=None
                if ca.gigfinder.name == "datakunstenbe":
                    ca.artist = None
                    ca.gigfinder = None
                    ca.raw_venue = None
                    ca.delete()
                else:
                    ca.save(update_fields=["concert"])

            for relconcertartist in RelationConcertArtist.objects.filter(concert=concert):
                relconcertartist.artist=None
                relconcertartist.concert=None
                relconcertartist.delete()

            for relconcertorganisation in RelationConcertOrganisation.objects.filter(concert=concert):
                relconcertorganisation.organisation = None
                relconcertorganisation.concert = None
                relconcertorganisation.delete()

            for relconcertconcert in RelationConcertConcert.objects.filter(concert_a=concert):
                relconcertconcert.concert_a = None
                relconcertconcert.concert_b = None
                relconcertconcert.delete()

            concert.delete()

        for concert in Concert.objects.filter(concertannouncement__gigfinder__name="podiumfestivalinfo"):
            print(concert, concert.pk)
            for ca in ConcertAnnouncement.objects.filter(concert=concert):
                ca.concert=None
                if ca.gigfinder.name == "podiumfestivalinfo":
                    ca.artist = None
                    ca.gigfinder = None
                    ca.raw_venue = None
                    ca.delete()
                else:
                    ca.save(update_fields=["concert"])

            for relconcertartist in RelationConcertArtist.objects.filter(concert=concert):
                relconcertartist.artist = None
                relconcertartist.concert = None
                relconcertartist.delete()

            for relconcertorganisation in RelationConcertOrganisation.objects.filter(concert=concert):
                relconcertorganisation.organisation = None
                relconcertorganisation.concert = None
                relconcertorganisation.delete()

            for relconcertconcert in RelationConcertConcert.objects.filter(concert_a=concert):
                relconcertconcert.concert_a = None
                relconcertconcert.concert_b = None
                relconcertconcert.delete()

            concert.delete()

