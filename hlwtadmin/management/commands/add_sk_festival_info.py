from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from pandas import read_excel


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        latest = read_excel("latest.xlsx")

        sk_festivals = latest[(latest["source"] == "songkick") & (latest["event_type"] == "festival")]

        for row in sk_festivals.iterrows():
            gigfinder_id = row[1]["event_id"].lstrip("songkick_")
            ca = ConcertAnnouncement.objects.filter(gigfinder__name="www.songkick.com").filter(gigfinder_concert_id=gigfinder_id).first()
            print(ca.id, ca)
            ca.is_festival = True
            ca.until_date = row[1]["einddatum"]
            ca.save(update_fields=['is_festival', 'until_date'])

            concert = ca.concert
            print(concert.id, concert)
            if concert:
                concert.until_date = row[1]["einddatum"]
                concert.save(update_fields=['until_date'])

                rels = RelationConcertOrganisation.objects.filter(concert=concert.id)
                for rel in rels:
                    rel.organisation.organisation_type.add(2)
            input()
