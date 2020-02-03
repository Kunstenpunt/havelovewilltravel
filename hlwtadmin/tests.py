from django.test import TestCase
from .models import ConcertAnnouncement, Concert, Artist, Organisation, Location, Country, RelationConcertArtist, RelationConcertOrganisation, Venue, GigFinder, GigFinderUrl

from havelovewilltravel.hlwtadmin.management.commands.synchronize_with_musicbrainz import synchronize_concerts_per_artist, synchronize_with_musicbrainz
from background_task.tasks import tasks


# Create your tests here.
class ConcertAnnouncementTest(TestCase):
    def setUp(self):
        self.gigfinder = GigFinder.objects.create(name="songkick",
                                                  base_url="http://www.songkick.com",
                                                  api_key="1234")
        self.gigfinder.save()
        self.artist = Artist.objects.create(name="testmans",
                                            disambiguation="een test artiest",
                                            mbid="mbid")
        self.artist.save()
        self.gigfinderurl = GigFinderUrl.objects.create(artist=self.artist,
                                                        gigfinder=self.gigfinder,
                                                        url="http://www.songkick.com/a/1234")
        self.gigfinderurl.save()
        self.country = Country.objects.create(name="testland")
        self.country.save()
        self.location = Location.objects.create(city="teststad",
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

        self.venue = Venue.objects.create(raw_venue="testvenue | songkick",
                                          raw_location="brussel, belgique",
                                          organisation=self.organisation)
        self.venue.save()

        self.venue2 = Venue.objects.create(raw_venue="testvenue2 | songkick",
                                          raw_location="brussel, belgique",
                                          organisation=self.organisation2)
        self.venue2.save()

        self.venue_without_organisation = Venue.objects.create(raw_venue="testvenue zonder org | songkick",
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
        self.assertEqual(self.rel_concert_organisation.organisation, ca.raw_venue.organisation)

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

    def test_concertannouncement_without_existing_concert(self):
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

    def test_concertannouncement_with_raw_venue_without_organisation_and_without_existing_concert(self):
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


class MyBackgroundTaskTestCase(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="Rebirth",
                                            disambiguation="een test artiest",
                                            mbid="f10f583b-c16b-4c36-9bec-916f3af7fa95")
        self.artist.save()

        self.gf = GigFinder.objects.create(name="facebook.com",
                                           base_url="https://www.facebook.com/",
                                           api_key="1234")
        self.gf.save()

        self.gfurl = GigFinderUrl(artist=self.artist,
                                  gigfinder=self.gf,
                                  url="https://www.facebook.com/rebirthcollective")
        self.gfurl.save()

    def test_synchronize_with_musicbrainz(self):
        synchronize_with_musicbrainz()
        tasks.run_next_task()
        self.assertEqual(Artist.objects.count(), 9)
        self.assertEqual(GigFinderUrl.objects.count(), 7)
        self.assertTrue(Artist.objects.filter(name="Rebirth Collective").first().include)

    def test_synchronize_concerts_per_artist(self):
        synchronize_concerts_per_artist()
        tasks.run_next_task()
        self.assertEqual(Concert.objects.count(), ConcertAnnouncement.objects.count())

