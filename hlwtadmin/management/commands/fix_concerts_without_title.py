from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertOrganisation, RelationConcertArtist

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concert in Concert.objects.filter(title_iexact="nan") | Concert.objects.filter(title_iexact="none"):
            org = RelationConcertOrganisation.objects.filter(concert=concert).first().organisation
            artist = RelationConcertArtist.objects.filter(concert=concert).first().artist
            generated_title = artist.name + " @ " + org.name
            print(generated_title)
            concert.title = generated_title
            concert.save()
