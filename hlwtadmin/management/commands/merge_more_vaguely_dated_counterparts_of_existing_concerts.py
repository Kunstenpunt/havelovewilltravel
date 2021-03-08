from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from collections import Counter

from django.db.models import Prefetch


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # get all concerts from all organisations
        concerts = Concert.objects.all(
                    ).prefetch_related(
                        Prefetch('organisation', Organisation.objects.all(), to_attr='related_organisations'),
                        Prefetch('artist', Artist.objects.all(), to_attr='related_artists')
                        )#.distinct() ?

        # check whether single date exists?
        progress = 0
        total = len(concerts)
        print(f'Total concerts: {total}')
        for concert in concerts:
            progress += 1
            if progress % 1000 == 0:
                print(f'{progress}/{total}')
            checked_tuples = []
            for artist in concert.related_artists:
                for organisation in concert.related_organisations:
                        possible_duplicates = Concert.objects.filter(artist=artist, organisation=organisation)
                        for candidate in possible_duplicates:
                            duplicates = possible_duplicates.filter(title=candidate.title)
                            if len(duplicates) > 1:
                                specifics = []
                                longer = []
                                for d in duplicates:
                                    if d.until_date:
                                        if d.until_date != d.date:
                                            longer.append(d)
                                        else:
                                            specifics.append(d)
                                    else:
                                        specifics.append(d)
                                if longer and specifics:
                                    for l in longer:
                                        for s in specifics:
                                            if l.date <= s.date <= l.until_date:
                                                try:
                                                    concert_merge = ConcertsMerge.objects.create(primary_object=s)
                                                    concert_merge.alias_objects.set(l)
                                                    concert_merge.merge()
                                                    concert_merge.delete()
                                                except:
                                                    # already deleted
                                                    continue
                                '''
                                # logic to merge duplicate single concerts, Tom wrote something that is perhaps safer, or at least more restricted
                                existing_dates = []
                                if len(specifics) > 1:
                                    for s in specifics:
                                        if s.date in existing_dates:
                                            print('possible doubles?')
                                            print(s)
                                        else:
                                            existing_dates.append(s.date)
                                '''