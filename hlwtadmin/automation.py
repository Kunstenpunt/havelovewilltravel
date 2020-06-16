from .models import Artist, GigFinderUrl, GigFinder, ConcertAnnouncement, Venue, Location, Organisation, Country, Concert, RelationConcertConcert, RelationConcertOrganisation, RelationConcertArtist, Location


class ConcertannouncementToConcert:
    def __init__(self, concertannouncement):
        self.concertannouncement = concertannouncement
        self.masterconcert = None

    def automate(self):
        print("working on", self.concertannouncement, self.concertannouncement.pk)
        input()

        if self._concertannouncement_has_daterange():
            print("\tCA with date range")
            self.masterconcert = self._exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist()
            if self.masterconcert:
                print("\t\tfound a MC to relate to")
                self._relate_concertannouncement_to_masterconcert()
            else:
                print("\t\tmaking a new MC")
                if self._venue_is_not_related_to_organisation():
                    print("\t\t\tvenue has no organisation, so creating one")
                    self._create_new_unverified_organisation_and_relate_to_venue()
                self._create_new_masterconcert_with_concertannouncement_organisation_artist()
        else:
            print("\tCA has specific date")
            self.masterconcert = self._exists_non_cancelled_masterconcert_on_date_in_location_with_artist()
            if self.masterconcert:
                print("\t\tfound a MC to relate to")
                self._relate_concertannouncement_to_masterconcert()
                self._perhaps_specify_masterconcert_date()
                if self._venue_is_not_related_to_organisation():
                    print("\t\t\tvenue is not linked to an organisation, so making a new unverified organisation")
                    self._create_new_unverified_organisation_and_relate_to_venue()
                if self._is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert():
                    print("\t\t\tattach the organisation of the venue to the concert")
                    self._relate_organisation_related_to_venue_also_to_the_masterconcert()
            else:
                print("\t\tmaking new MC")
                if self._venue_is_not_related_to_organisation():
                    print("\t\t\tcreate a new organisation for the venue and concert")
                    self._create_new_unverified_organisation_and_relate_to_venue()
                self._create_new_masterconcert_with_concertannouncement_organisation_artist()
        input()

    def _concertannouncement_has_daterange(self):
        return self.concertannouncement.date < self.concertannouncement.until_date if self.concertannouncement.until_date else False

    def venue_organisation_is_in_concert_related_organisation(self):
        orgs = set(RelationConcertOrganisation.objects.filter(concert=self.concertannouncement.concert).values_list("organisation", flat=True))
        return self.concertannouncement.raw_venue.organisation.pk in orgs

    def _exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist(self):
        period_concert = Concert.objects.\
            filter(until_date__isnull=False).\
            filter(date__lte=self.concertannouncement.date).\
            filter(until_date__gte=self.concertannouncement.until_date).\
            exclude(ignore=True).\
            exclude(cancelled=True).\
            filter(relationconcertartist__artist=self.concertannouncement.artist).\
            filter(relationconcertorganisation__organisation__location=self.concertannouncement.most_likely_clean_location())
        if period_concert:
            return period_concert.first()
        else:
            specific_concert = Concert.objects.\
                filter(until_date__isnull=True).\
                filter(date__gte=self.concertannouncement.date).\
                filter(date__lte=self.concertannouncement.until_date).\
                exclude(ignore=True).\
                exclude(cancelled=True).\
                filter(relationconcertartist__artist=self.concertannouncement.artist).\
                filter(relationconcertorganisation__organisation__location=self.concertannouncement.most_likely_clean_location())
            if specific_concert:
                return specific_concert.first()
            else:
                return None

    def _exists_non_cancelled_masterconcert_on_date_in_location_with_artist(self):
        period_concert = Concert.objects.\
            filter(until_date__isnull=False).\
            filter(date__lte=self.concertannouncement.date).\
            filter(until_date__gte=self.concertannouncement.date).\
            exclude(ignore=True).\
            exclude(cancelled=True).\
            filter(relationconcertartist__artist=self.concertannouncement.artist).\
            filter(relationconcertorganisation__organisation__location=self.concertannouncement.most_likely_clean_location())
        if period_concert:
            return period_concert.first()
        else:
            specific_concert = Concert.objects.\
                filter(until_date__isnull=True).\
                filter(date=self.concertannouncement.date).\
                exclude(ignore=True).\
                exclude(cancelled=True).\
                filter(relationconcertartist__artist=self.concertannouncement.artist).\
                filter(relationconcertorganisation__organisation__location=self.concertannouncement.most_likely_clean_location())
            if specific_concert:
                return specific_concert.first()
            else:
                return None

    def _is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self):
        rel = RelationConcertOrganisation.objects.\
            filter(concert=self.masterconcert).\
            filter(organisation=self.concertannouncement.raw_venue.organisation).first()
        return rel is not None

    def _relate_concertannouncement_to_masterconcert(self):
        self.concertannouncement.concert = self.masterconcert
        self.concertannouncement.save()

    def _perhaps_specify_masterconcert_date(self):
        if self.concertannouncement.concert.until_date:
            print("----specifying masterconcert date")
            self.concertannouncement.concert.date = self.date
            self.concertannouncement.concert.until_date = None
            self.concertannouncement.concert.save()

    def _relate_organisation_related_to_venue_also_to_the_masterconcert(self):
        if not self.concertannouncement.raw_venue.non_assignable and self.concertannouncement.raw_venue.organisation is not None:
            print("----attaching assignable organisation from venue to concert")
            rco = RelationConcertOrganisation.objects.\
                create(concert=self.masterconcert,
                       organisation=self.concertannouncement.raw_venue.organisation,
                       verified=False)
            rco.save()

    def _relate_organisation_related_to_masterconcert_to_venue(self):
        if not self.concertannouncement.raw_venue.non_assignable and self.concertannouncement.raw_venue.organisation is None:
            org = RelationConcertOrganisation.objects.filter(concert=self.masterconcert).first()
            if org:
                if org.location == self.clean_location_from_string():
                    print("----attach organisation of concert to assignable venue without organisation")
                    self.concertannouncement.raw_venue.organisation = org.organisation
                    self.concertannouncement.raw_venue.save()

    def _venue_is_not_related_to_organisation(self):
        if not self.concertannouncement.raw_venue.non_assignable:
            return self.concertannouncement.raw_venue.organisation is None
        else:
            return False

    def _create_new_unverified_organisation_and_relate_to_venue(self):
        try:
            name_prop, stad, land, bron = self.concertannouncement.raw_venue.raw_venue.split("|")
            name = name_prop if len(name_prop.strip()) > 0 else self.concertannouncement.raw_venue.raw_venue
            loc = None
            org = None
            if land.lower() != "none" or stad.lower() != "none" or land != "" or stad != "":
                if name not in ("None", "nan"):
                    country = Country.objects.filter(name=land).first()
                    if not country:
                        country = Country.objects.filter(iso_code__iexact=land.lower()).first()
                    loc = Location.objects.\
                        filter(city__istartswith=stad).\
                        filter(country=country).\
                        first()
                    org = Organisation.objects.\
                        create(name=name,
                               sort_name=name,
                               annotation=(stad if len(stad.strip()) > 0 else "unknown city") + ", " + (land if len(land.strip()) else "unknown country") + " (" + bron + ")",
                               location=loc,
                               verified=False)
                    org.save()
                if self.concertannouncement.raw_venue.organisation is None and not self.concertannouncement.raw_venue.non_assignable and org is not None:
                    self.concertannouncement.raw_venue.organisation = org
                    self.concertannouncement.raw_venue.save()
        except ValueError as e:
            print("----something went wrong", e)
            pass

    def _create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        mc = Concert.objects.\
            create(title=self.concertannouncement.title,
                   date=self.concertannouncement.date,
                   until_date=(self.concertannouncement.until_date if self.concertannouncement.until_date else None),
                   latitude=self.concertannouncement.latitude,
                   longitude=self.concertannouncement.longitude)
        mc.save()
        for genre in self.concertannouncement.artist.genre.all():
            mc.genre.add(genre)
        if self.concertannouncement.raw_venue.organisation:
            relco = RelationConcertOrganisation(concert=mc, organisation=self.concertannouncement.raw_venue.organisation, verified=False)
            relco.save()
        relca = RelationConcertArtist(concert=mc, artist=self.concertannouncement.artist)
        relca.save()
        self.concertannouncement.concert = mc
        self.concertannouncement.save()
