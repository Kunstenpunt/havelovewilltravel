from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location, LocationsMerge, ConcertsMerge

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Count


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        handled = set()
        for relation in RelationConcertArtist.objects.filter(concert__until_date__isnull=True).exclude(concert__verified=True).order_by('concert__date'):
            concert_a = relation.concert
            if concert_a.pk not in handled:
                handled.add(concert_a.pk)
                organisation = concert_a.organisationsqs().first().organisation
                location = organisation.location
                artist = relation.artist
                print(concert_a.pk, concert_a.date, artist.name, organisation.name, location)
                alias_objects = []
                for concert_b in Concert.objects.exclude(pk=concert_a.pk).exclude(verified=True).filter(relationconcertartist__artist=artist).filter(relationconcertorganisation__organisation__location=location).order_by('date'):
                    if concert_b.pk not in handled:
                        handled.add(concert_b.pk)
                        if concert_b.until_date is None:
                            if concert_a.date == concert_b.date:
                                print("\tcould merge with", concert_b.pk, concert_b.date, concert_b.until_date, concert_b.artists(), concert_b.organisations())
                                alias_objects.append(concert_b)
                        else:
                            if concert_b.date <= concert_a.date <=concert_b.until_date:
                                print("\tcould merge with", concert_b.pk, concert_b.date, concert_b.until_date, concert_b.artists(), concert_b.organisations())
                                alias_objects.append(concert_b)
                if len(alias_objects) > 0:
                    cm = ConcertsMerge.objects.filter(primary_object=concert_a).first()
                    if cm is None:
                        cm = ConcertsMerge.objects.create(
                            primary_object=concert_a
                        )
                        cm.save()
                    for alias_object in alias_objects:
                        if alias_object not in cm.alias_objects.all():
                            cm.alias_objects.add(alias_object)
                    input()
