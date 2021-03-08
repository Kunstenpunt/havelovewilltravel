from hlwtadmin.models import ConcertAnnouncement, Concert, Organisation, RelationConcertOrganisation

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Prefetch
import pandas as pd
# concertannouncement 

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        concert_announcements = ConcertAnnouncement.objects.all(
                    ).prefetch_related(
                        Prefetch('concert', Concert.objects.all(), to_attr='related_concert'),
                        )
        cnt = 0
        cnt_empty_org = 0
        for ca in concert_announcements:
            if ca.description != None:
                cnt += 1
                if ca.related_concert:
                    if not ca.related_concert.organisationsqs():
                        cnt_empty_org += 1
                        print(ca.description)
        #print(cnt)
        #print(cnt_empty_org)