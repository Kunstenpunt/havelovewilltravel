from hlwtadmin.models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for concertannouncement in ConcertAnnouncement.objects.filter(concert__isnull=True).exclude(ignore=True).filter(id=189402):
            print("working on", concertannouncement, concertannouncement.pk)
            input()

            if self._concertannouncement_has_daterange(concertannouncement):
                print("\tCA with date range")
                masterconcert = self._exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist(concertannouncement)
                if masterconcert:
                    print("\t\tfound a MC to relate to")
                    self._relate_concertannouncement_to_masterconcert(concertannouncement, masterconcert)
                else:
                    print("\t\tmaking a new MC")
                    if self._venue_is_not_related_to_organisation(concertannouncement):
                        self._create_new_unverified_organisation_and_relate_to_venue(concertannouncement)
                    self._create_new_masterconcert_with_concertannouncement_organisation_artist(concertannouncement)
            else:
                print("\tCA has specific date")
                masterconcert = self._exists_non_cancelled_masterconcert_on_date_in_location_with_artist(concertannouncement)
                if masterconcert:
                    print("\t\tfound a MC to relate to")
                    self._relate_concertannouncement_to_masterconcert(concertannouncement, masterconcert)
                    self._perhaps_specify_masterconcert_date(concertannouncement)
                    if self._is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(concertannouncement, masterconcert):
                        print("\t\t\tattach the organisation of the venue to the concert")
                        self._relate_organisation_related_to_venue_also_to_the_masterconcert(concertannouncement, masterconcert)
                    else:
                        print("\t\t\tattach the organisation of the concert to the venue")
                        self._relate_organisation_related_to_masterconcert_to_venue(concertannouncement, masterconcert)
                else:
                    print("\t\tmaking new MC")
                    if self._venue_is_not_related_to_organisation(concertannouncement):
                        print("\t\t\tcreate a new organisation for the venue and concert")
                        self._create_new_unverified_organisation_and_relate_to_venue(concertannouncement)
                    self._create_new_masterconcert_with_concertannouncement_organisation_artist(concertannouncement)
            input()

    @staticmethod
    def _concertannouncement_has_daterange(self):
        return self.date < self.until_date if self.until_date else False

    @staticmethod
    def venue_organisation_is_in_concert_related_organisation(self):
        orgs = set(RelationConcertOrganisation.objects.filter(concert=self.concert).values_list("organisation", flat=True))
        return self.raw_venue.organisation.pk in orgs

    @staticmethod
    def _exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist(self):
        period_concert = Concert.objects.exclude(until_date__isnull=True).filter(date__lte=self.date).filter(
                    until_date__gte=self.until_date).exclude(ignore=True).exclude(cancelled=True).filter(
                    relationconcertartist__artist=self.artist).filter(
                    relationconcertorganisation__organisation__location=self.most_likely_clean_location())
        if period_concert:
            return period_concert.first()
        else:
            specific_concert = Concert.objects.filter(until_date__isnull=True).filter(date__lte=self.date).filter(
                    date__gte=self.until_date).exclude(ignore=True).exclude(cancelled=True).filter(
                    relationconcertartist__artist=self.artist).filter(
                    relationconcertorganisation__organisation__location=self.most_likely_clean_location())
            if specific_concert:
                return specific_concert.first()
            else:
                return None

    @staticmethod
    def _exists_non_cancelled_masterconcert_on_date_in_location_with_artist(self):
        period_concert = Concert.objects.filter(until_date__isnull=False).filter(date__lte=self.date).filter(
            until_date__gte=self.date).exclude(ignore=True).exclude(cancelled=True).filter(
            relationconcertartist__artist=self.artist).filter(
            relationconcertorganisation__organisation__location=self.most_likely_clean_location())
        if period_concert:
            return period_concert.first()
        else:
            specific_concert = Concert.objects.filter(until_date__isnull=True).filter(date=self.date).exclude(
                ignore=True).exclude(cancelled=True).filter(relationconcertartist__artist=self.artist).filter(
                relationconcertorganisation__organisation__location=self.most_likely_clean_location())
            if specific_concert:
                return specific_concert.first()
            else:
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
    def _perhaps_specify_masterconcert_date(self):
        if self.concert.until_date:
            print("----specifying masterconcert date")
            self.concert.date = self.date
            self.concert.until_date = None
            self.concert.save()

    @staticmethod
    def _relate_organisation_related_to_venue_also_to_the_masterconcert(self, masterconcert):
        if not self.raw_venue.non_assignable and self.raw_venue.organisation is not None:
            print("----attaching assignable organisation fro mvenue to concert")
            rco = RelationConcertOrganisation.objects.create(
                concert=masterconcert,
                organisation=self.raw_venue.organisation,
                verified=False)
            rco.save()

    @staticmethod
    def _relate_organisation_related_to_masterconcert_to_venue(self, masterconcert):
        if not self.raw_venue.non_assignable and self.raw_venue.organisation is None:
            org = RelationConcertOrganisation.objects.filter(concert=masterconcert).first()
            if org:
                if org.location == self.clean_location_from_string():
                    print("----attach organisation of concert to assignable venue without organisation")
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
            loc = None
            org = None
            if land.lower() != "none" or stad.lower() != "none" or land != "" or stad != "":
                if name not in ("None", "nan"):
                    country = Country.objects.filter(name=land).first()
                    if not country:
                        country = Country.objects.filter(iso_code__iexact=land.lower()).first()
                    loc = Location.objects.filter(city__istartswith=stad).filter(country=country).first()
                    org = Organisation.objects.create(name=name, sort_name=name,
                                                      annotation=(stad if len(stad.strip()) > 0 else "unknown city") + ", " + (land if len(land.strip()) else "unknown country") + " (" + bron + ")",
                                                      location=loc, verified=False)
                    org.save()
                if self.raw_venue.organisation is None and not self.raw_venue.non_assignable and org is not None:
                    self.raw_venue.organisation = org
                    self.raw_venue.save()
        except ValueError as e:
            print("----something went wrong", e)
            pass

    @staticmethod
    def _create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        mc = Concert.objects.create(title=self.title, date=self.date, until_date=(self.until_date if self.until_date else None), latitude=self.latitude, longitude=self.longitude)
        mc.save()
        for genre in self.artist.genre.all():
            mc.genre.add(genre)
        relco = RelationConcertOrganisation(concert=mc, organisation=self.raw_venue.organisation, verified=False)
        relco.save()
        relca = RelationConcertArtist(concert=mc, artist=self.artist)
        relca.save()
        self.concert = mc
        self.save()
