from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True).filter(id=34273):
            print("working on", concertannouncement, concertannouncement.pk)
            masterconcert = self._exists_non_cancelled_masterconcert_on_date_with_artist(concertannouncement)
            if masterconcert:
                print("found a masterconcert", masterconcert, masterconcert.pk)
                if masterconcert.title == "nan":
                    masterconcert.title = concertannouncement.title
                    masterconcert.save()
                self._relate_concertannouncement_to_masterconcert(concertannouncement, masterconcert)
                if self._is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(concertannouncement, masterconcert):
                    self._relate_organisation_related_to_venue_also_to_the_masterconcert(concertannouncement, masterconcert)
                else:
                    self._relate_organisation_related_to_masterconcert_to_venue(concertannouncement, masterconcert)
            else:
                print("not found anything, making something from scratch")
                if self._venue_is_not_related_to_organisation(concertannouncement):
                    self._create_new_unverified_organisation_and_relate_to_venue(concertannouncement)
                self._create_new_masterconcert_with_concertannouncement_organisation_artist(concertannouncement)

    @staticmethod
    def _exists_non_cancelled_masterconcert_on_date_with_artist(self):
        try:
            return Concert.objects.filter(date=self.date).exclude(ignore=True).exclude(cancelled=True).filter(
                relationconcertartist__artist=self.artist).filter(
                relationconcertorganisation__organisation__location=self.most_likely_clean_location()).first()
        except IndexError:
            return None

    @staticmethod
    def _is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self, masterconcert):
        rel = RelationConcertOrganisation.objects.filter(concert=masterconcert).filter(organisation=self.raw_venue.organisation).first()
        return rel is not None

    @staticmethod
    def _relate_concertannouncement_to_masterconcert(self, masterconcert):
        self.concert = masterconcert
        self.save()

    @staticmethod
    def _relate_organisation_related_to_venue_also_to_the_masterconcert(self, masterconcert):
        if not self.raw_venue.non_assignable and self.raw_venue.organisation is not None:
            rco = RelationConcertOrganisation.objects.create(
                concert=masterconcert,
                organisation=self.raw_venue.organisation,
                verified=False)
            rco.save()

    @staticmethod
    def _relate_organisation_related_to_masterconcert_to_venue(self, masterconcert):
        if not self.raw_venue.non_assignable:
            org = RelationConcertOrganisation.objects.filter(concert=masterconcert).first()
            if org:
                self.raw_venue.organisation = org.organisation
                self.raw_venue.save()

    @staticmethod
    def _venue_is_not_related_to_organisation(self):
        if not self.raw_venue.non_assignable:
            return self.raw_venue.organisation is None
        else:
            return False

    @staticmethod
    def _create_new_unverified_organisation_and_relate_to_venue(self):
        try:
            name_prop, stad, land, bron = self.raw_venue.raw_venue.split("|")
            name = name_prop if len(name_prop.strip()) > 0 else self.raw_venue.raw_venue
            if name not in ("None", "nan"):
                country = Country.objects.filter(name=land).first()
                if not country:
                    country = Country.objects.filter(iso_code=land.lower()).first()
                loc = Location.objects.filter(city__istartswith=stad).filter(country=country).first()
                org = Organisation.objects.create(name=name,
                                                  annotation=(stad if len(stad.strip()) > 0 else "unknown city") + ", " + (land if len(land.strip()) else "unknown country") + " (" + bron + ")",
                                                  location=loc, verified=False)
                org.save()
                if self.raw_venue.organisation is None and not self.raw_venue.non_assignable:
                    self.raw_venue.organisation = org
                    self.raw_venue.save()
        except ValueError:
            pass

    @staticmethod
    def _create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        mc = Concert.objects.create(title=self.title, date=self.date, latitude=self.latitude, longitude=self.longitude)
        mc.save()
        for genre in self.artist.genre.all():
            mc.genre.add(genre)
        relco = RelationConcertOrganisation(concert=mc, organisation=self.raw_venue.organisation, verified=False)
        relco.save()
        relca = RelationConcertArtist(concert=mc, artist=self.artist)
        relca.save()
        self.concert = mc
        self.save()
