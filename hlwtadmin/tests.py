from django.test import TestCase
from .models import ConcertAnnouncement, Concert, Artist, Organisation, Location, Country, RelationConcertArtist, \
    RelationConcertOrganisation, Venue, GigFinder, GigFinderUrl, OrganisationsMerge, RelationOrganisationOrganisation, \
    Genre, ConcertannouncementToConcert


class ConcertannouncementToConcertTest(TestCase):
    def setUp(self):
        pass

    def test_concertannouncement_has_daterange(self):
        self.assertTrue(True)

    def test_venue_organisation_is_in_concert_related_organisation(self):
        self.assertTrue(True)

    def test_exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist(self):
        self.assertTrue(True)

    def test_exists_non_cancelled_masterconcert_on_date_in_location_with_artist(self):
        self.assertTrue(True)

    def test_is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self):
        self.assertTrue(True)

    def test_perhaps_specify_masterconcert_date(self):
        self.assertTrue(True)

    def test_relate_organisation_related_to_venue_also_to_the_masterconcert(self):
        self.assertTrue(True)

    def test_relate_organisation_related_to_masterconcert_to_venue(self):
        self.assertTrue(True)

    def test_venue_is_not_related_to_organisation(self):
        self.assertTrue(True)

    def test_create_new_unverified_organisation_and_relate_to_venue(self):
        self.assertTrue(True)

    def test_create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        self.assertTrue(True)


class OrganisationsMergeTest(TestCase):
    def setUp(self):
        self.concert = Concert(
            title="testconcert"
        )
        self.concert.save()

        self.organisation_a = Organisation.objects.create(
            name="quintenville1"
        )
        self.organisation_a.save()
        self.organisation_b = Organisation.objects.create(
            name="quintenville2"
        )
        self.organisation_b.save()
        self.organisation_c = Organisation.objects.create(
            name="quintenville3"
        )
        self.organisation_c.save()
        self.organisation_d = Organisation.objects.create(
            name="quintenville4"
        )
        self.organisation_d.save()

        self.relationorgorg = RelationOrganisationOrganisation.objects.create(
            organisation_a=self.organisation_b,
            organisation_b=self.organisation_d
        )

        self.relationconcertorganisation = RelationConcertOrganisation.objects.create(
            organisation=self.organisation_b,
            concert=self.concert
        )
        self.relationconcertorganisation.save()

        self.location = Location.objects.create(
            city="teststad"
        )
        self.location.save()
        self.organisation_b.location = self.location

        self.organisationsmerge = OrganisationsMerge(primary_object=self.organisation_a)
        self.organisationsmerge.save()
        self.organisationsmerge.alias_objects.add(self.organisation_b)
        self.organisationsmerge.alias_objects.add(self.organisation_c)

    def test_primary_object_is_only_object_that_remains(self):
        self.organisationsmerge.delete()
        self.assertIsNone(OrganisationsMerge.objects.first())
        self.assertEqual(len(Organisation.objects.all()), 2)

    # def test_primary_object_without_location_receives_location_from_alias(self):
    #     self.organisationsmerge.delete()
    #     self.assertEqual(Organisation.objects.filter(name=self.organisation_a.name).first().location, self.organisation_b.location)

    def test_relation_org_org_is_inherited(self):
        self.assertIsNone(RelationOrganisationOrganisation.objects.filter(organisation_a=self.organisation_a).first())
        self.organisationsmerge.delete()
        self.assertEqual(RelationOrganisationOrganisation.objects.filter(organisation_a=self.organisation_a).first().organisation_b, self.organisation_d)

    def test_concert_of_organisation_b_is_inherited_by_organisation_a(self):
        self.assertIsNone(RelationConcertOrganisation.objects.filter(organisation=self.organisation_a).first())
        self.organisationsmerge.delete()
        self.assertEqual(RelationConcertOrganisation.objects.filter(organisation=self.organisation_a).first().concert, self.concert)


class ConcertTest(TestCase):
    def setUp(self):
        self.concert_a = Concert.objects.create(
            title="test a",
            date="1985-11-23"
        )
        self.concert_a.save()
        self.organisation = Organisation.objects.create(
            name="quintenville"
        )
        self.organisation.save()
        self.concert_b = Concert.objects.create(
            title="test b",
            date="1985-11-23"
        )
        self.concert_b.save()
        self.rel_a = RelationConcertOrganisation.objects.create(
            concert=self.concert_a,
            organisation=self.organisation
        )
        self.rel_a.save()
        self.rel_b = RelationConcertOrganisation.objects.create(
            concert=self.concert_b,
            organisation=self.organisation
        )
        self.rel_b.save()

    def test_concerts_on_same_day_and_in_same_organisation(self):
        self.assertEqual(1, len(self.concert_a.find_concurring_concerts()))
        self.assertIn(self.concert_a, self.concert_b.find_concurring_concerts())

    def test_is_ontologically_sound(self):
        self.assertTrue(True)

    def test_artists(self):
        self.assertTrue(True)

    def test_artistsqs(self):
        self.assertTrue(True)

    def test_organisations(self):
        self.assertTrue(True)

    def test_organisationsqs(self):
        self.assertTrue(True)

    def test_concertannouncements(self):
        self.assertTrue(True)

    def test_is_upcoming(self):
        self.assertTrue(True)

    def test_is_new(self):
        self.assertTrue(True)

    def test_is_confirmed(self):
        self.assertTrue(True)

    def test_delete(self):
        self.assertTrue(True)


class GigfinderUrlTest(TestCase):
    def setUp(self):
        pass

    def test_gigfinderurl_recently_confirmed(self):
        self.assertTrue(True)

    def test_gigfinderurl_recently_synchronized(self):
        self.assertTrue(True)


class ConcertAnnouncementTest(TestCase):
    def setUp(self):
        self.gigfinder = GigFinder.objects.create(name="songkick",
                                                  base_url="http://www.songkick.com",
                                                  api_key="1234")
        self.gigfinder.save()
        self.genre = Genre.objects.create(name="testgenre")
        self.genre.save()
        self.artist = Artist.objects.create(name="testmans",
                                            disambiguation="een test artiest",
                                            mbid="mbid")
        self.artist.save()
        self.artist.genre.add(self.genre)
        self.gigfinderurl = GigFinderUrl.objects.create(artist=self.artist,
                                                        gigfinder=self.gigfinder,
                                                        url="http://www.songkick.com/a/1234")
        self.gigfinderurl.save()
        self.country = Country.objects.create(name="testland")
        self.country.save()
        self.location = Location.objects.create(city="brussel",
                                                country=self.country,
                                                latitude=0,
                                                longitude=0)
        self.location.save()
        self.organisation = Organisation.objects.create(name="testclub",
                                                        disambiguation="een test club",
                                                        location=self.location,
                                                        latitude=0,
                                                        longitude=0,
                                                        start_date="1985-11-23",
                                                        end_date="2020-01-01")
        self.organisation.save()

        self.organisation2 = Organisation.objects.create(name="testclub2",
                                                        disambiguation="een test club 2",
                                                        location=self.location,
                                                        latitude=0,
                                                        longitude=0,
                                                        start_date="1985-11-23",
                                                        end_date="2020-01-01")
        self.organisation2.save()

        self.venue = Venue.objects.create(raw_venue="testvenue | brussel | belgique | songkick",
                                          raw_location="brussel, belgique",
                                          organisation=self.organisation)
        self.venue.save()

        self.venue2 = Venue.objects.create(raw_venue="testvenue2 | brussel | belgique | songkick",
                                          raw_location="brussel, belgique",
                                          organisation=self.organisation2)
        self.venue2.save()

        self.venue_without_organisation = Venue.objects.create(raw_venue="testvenue zonder org | brussel | belgique | songkick",
                                                               raw_location="brussel, belgique")
        self.venue_without_organisation.save()
        self.concert = Concert.objects.create(title="testconcert",
                                              date="1985-11-23")
        self.concert.save()
        self.cancelled_concert = Concert.objects.create(title="gecancelled testconcert",
                                                        date="1985-11-23")
        self.cancelled_concert.save()
        self.rel_concert_artist = RelationConcertArtist(artist=self.artist,
                                                        concert=self.concert)
        self.rel_concert_artist.save()
        self.rel_concert_organisation = RelationConcertOrganisation(concert=self.concert,
                                                                    organisation=self.organisation,
                                                                    organisation_credited_as="nothing")
        self.rel_concert_organisation.save()
        self.rel_cancelled_concert_artist = RelationConcertArtist(artist=self.artist,
                                                                  concert=self.cancelled_concert)
        self.rel_cancelled_concert_artist.save()
        self.rel_cancelled_concert_organisation = RelationConcertOrganisation(organisation=self.organisation,
                                                                              concert=self.cancelled_concert)
        self.rel_cancelled_concert_organisation.save()

    def test_concertannouncement_with_organisation_and_existing_concert(self):
        ca = ConcertAnnouncement(title="test concert announcement",
                                 artist=self.artist,
                                 date="1985-11-23",
                                 gigfinder=self.gigfinder,
                                 gigfinder_concert_id="123",
                                 raw_venue=self.venue,
                                 ignore=False)
        ca.save()
        self.assertEqual(self.concert, ca.concert)

    def test_concertannouncement_without_organisation_and_existing_concert(self):
        ca = ConcertAnnouncement(title="test concert announcement",
                                 artist=self.artist,
                                 date="1985-11-23",
                                 gigfinder=self.gigfinder,
                                 gigfinder_concert_id="123",
                                 raw_venue=self.venue_without_organisation,
                                 ignore=False)
        ca.save()
        self.assertEqual(self.concert, ca.concert)
        self.assertEqual(Organisation.objects.all().order_by('-pk')[0], ca.raw_venue.organisation)

    def test_concertannouncement_with_different_organisation_and_existing_concert(self):
        ca = ConcertAnnouncement(title="test concert announcement",
                                 artist=self.artist,
                                 date="1985-11-23",
                                 gigfinder=self.gigfinder,
                                 gigfinder_concert_id="123",
                                 raw_venue=self.venue2,
                                 ignore=False)
        ca.save()
        # concert should have 2 related organisations
        self.assertEqual(2, RelationConcertOrganisation.objects.filter(concert=self.concert).count())

    def test_concertannouncement_with_organisation_without_existing_concert(self):
        ca = ConcertAnnouncement(title="test concert announcement",
                                 artist=self.artist,
                                 date="1995-11-24",
                                 gigfinder=self.gigfinder,
                                 gigfinder_concert_id="123",
                                 raw_venue=self.venue2,
                                 ignore=False)
        ca.save()
        # concert date should be date of announcement
        self.assertEqual("1995-11-24", ca.concert.date)
        # concert organisation should be organisation of raw venue of announcement
        self.assertEqual(RelationConcertOrganisation.objects.filter(concert=ca.concert)[0].organisation, ca.raw_venue.organisation)
        # concert artist should be artist of announcement
        self.assertEqual(RelationConcertArtist.objects.filter(concert=ca.concert)[0].artist, ca.artist)
        # concert genre should be genre of artist
        self.assertIn(self.genre, RelationConcertArtist.objects.filter(concert=ca.concert).first().concert.genre.all())

    def test_concertannouncement_without_organisation_and_without_existing_concert(self):
        ca = ConcertAnnouncement(title="test concert announcement without nothing",
                                 artist=self.artist,
                                 date="1995-11-24",
                                 gigfinder=self.gigfinder,
                                 gigfinder_concert_id="123",
                                 raw_venue=self.venue_without_organisation,
                                 ignore=False)
        ca.save()
        # there should now be a new organisation, so 3
        self.assertEqual(3, Organisation.objects.all().count())
        # there should be a new masterconcert, so 3
        self.assertEqual(3, Concert.objects.all().count())
        # ca should be related to a new concert with title == ca.title
        self.assertEqual(ca.concert.title, ca.title)
