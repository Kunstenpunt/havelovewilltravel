from django.db import models
from django.urls import reverse


# Create your models here.
class GigFinder(models.Model):
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    api_key = models.CharField(max_length=500)

    def __str__(self):
        return self.name + " (" + self.base_url + ")"


class Artist(models.Model):
    name = models.CharField(max_length=200)
    disambiguation = models.CharField(max_length=200, blank=True, null=True)
    mbid = models.CharField(max_length=25, primary_key=True)
    include = models.BooleanField(default=False)
    exclude = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('artist_detail', args=[str(self.mbid)])

    class Meta:
        ordering = ['name']


class GigFinderUrl(models.Model):
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    gigfinder = models.ForeignKey("GigFinder", on_delete=models.PROTECT)
    url = models.URLField()

    def __str__(self):
        return self.url + " (" + str(self.artist) + ", " + str(self.gigfinder) + ")"


class ConcertAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    gigfinder = models.ForeignKey("GigFinder", on_delete=models.PROTECT)
    gigfinder_concert_id = models.URLField()
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT, blank=True, null=True)
    last_seen_on = models.DateField(auto_now=True)
    raw_venue = models.ForeignKey("Venue", on_delete=models.PROTECT, blank=True, null=True)
    ignore = models.BooleanField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('concertannouncement_detail', args=[str(self.id)])
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.masterconcert = self._exists_non_cancelled_masterconcert_on_date_with_artist()
            if self.masterconcert:
                self._relate_concertannouncement_to_masterconcert()
                if self._is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert():
                    self._relate_organisation_related_to_venue_also_to_the_masterconcert()
                else:
                    self._relate_organisation_related_to_masterconcert_to_venue()
            else:
                if self._venue_is_not_related_to_organisation():
                    self._create_new_unverified_organisation_and_relate_to_venue()
                self._create_new_masterconcert_with_concertannouncement_organisation_artist()
        super(ConcertAnnouncement, self).save(*args, **kwargs)

    class Meta:
        ordering = ['last_seen_on', '-date']

    def _exists_non_cancelled_masterconcert_on_date_with_artist(self):
        try:
            return Concert.objects.filter(date=self.date).filter(relationconcertartist__artist=self.artist)[0]  # TODO what if multiple masterconcerts
        except IndexError:
            return None

    def _is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self):
        masterconcert_organisations = [rel.organisation for rel in RelationConcertOrganisation.objects.filter(concert=self.masterconcert)]
        return self.raw_venue.organisation and self.raw_venue.organisation not in masterconcert_organisations

    def _relate_concertannouncement_to_masterconcert(self):
        self.concert = self.masterconcert

    def _relate_organisation_related_to_venue_also_to_the_masterconcert(self):
        RelationConcertOrganisation.objects.create(concert=self.masterconcert, organisation=self.raw_venue.organisation, unverified=True)

    def _relate_organisation_related_to_masterconcert_to_venue(self):
        org = RelationConcertOrganisation.objects.filter(concert=self.masterconcert)[0].organisation  # TODO what if several organisations connected to masterconcert?
        self.raw_venue.organisation = org

    def _venue_is_not_related_to_organisation(self):
        return self.raw_venue.organisation is None

    def _create_new_unverified_organisation_and_relate_to_venue(self):
        org = Organisation.objects.create(name=self.raw_venue.raw_venue)
        org.save()
        self.raw_venue.organisation = org
        self.raw_venue.save()

    def _create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        mc = Concert.objects.create(title=self.title, date=self.date)
        mc.save()
        relco = RelationConcertOrganisation(concert=mc, organisation=self.raw_venue.organisation, unverified=True)
        relco.save()
        relca = RelationConcertArtist(concert=mc, artist=self.artist)
        relca.save()
        self.concert = mc


class Venue(models.Model):
    raw_venue = models.CharField(max_length=200)
    raw_location = models.CharField(max_length=200, blank=True, null=True)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return self.raw_venue

    def get_absolute_url(self):
        return reverse('venue_detail', args=[str(self.id)])

    class Meta:
        ordering = ['raw_venue']


class Concert(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False, blank=True, null=True)
    verified = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('concert_detail', args=[str(self.id)])

    class Meta:
        ordering = ['-date']


class Organisation(models.Model):
    name = models.CharField(max_length=200)
    disambiguation = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.PROTECT, blank=True, null=True)
    organisation_type = models.ManyToManyField("OrganisationType", blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organisation_detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']


class OrganisationType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Location(models.Model):
    city = models.CharField(max_length=200)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    country = models.ForeignKey("Country", blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.city + ", " + (self.country.name if self.country else "No country provided")

    def get_absolute_url(self):
        return reverse('location_detail', args=[str(self.id)])

    class Meta:
        ordering = ['country', 'city']


class Country(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationConcertArtist(models.Model):
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    artist_credited_as = models.CharField(max_length=200, blank=True, null=True)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)

    def __str__(self):
        return self.concert.title + " - " + self.artist.name


class RelationConcertOrganisation(models.Model):
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT, blank=True, null=True)
    organisation_credited_as = models.CharField(max_length=200, blank=True, null=True)
    relation_type = models.ManyToManyField("RelationConcertOrganisationType", blank=True)
    unverified = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.concert.title + " " + (self.organisation_credited_as  + " (" + self.organisation.name + ")" if self.organisation_credited_as else self.organisation.name)


class RelationConcertOrganisationType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationOrganisationOrganisation(models.Model):
    organisation_a = models.ForeignKey("Organisation", on_delete=models.PROTECT, related_name='organisationa')
    organisation_b = models.ForeignKey("Organisation", on_delete=models.PROTECT, related_name='organisationb')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    relation_type = models.CharField(max_length=200)

    def __str__(self):
        return self.organisation_a.name + " " + self.relation_type + " " + self.organisation_b.name + " (" + self.start_date.isoformat() + "-" + self.end_date.isoformat() + ")"

    def get_absolute_url(self):
        return reverse('relationorganisationorganisation_update', args=[str(self.id)])


class RelationArtistArtist(models.Model):
    artist_a = models.ForeignKey("Artist", on_delete=models.PROTECT, related_name='artista')
    artist_b = models.ForeignKey("Artist", on_delete=models.PROTECT, related_name='artistb')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    relation_type = models.CharField(max_length=200)

    def __str__(self):
        return self.artist_a.name + " " + self.relation_type + " " + self.artist_b.name + " (" + self.start_date.isoformat() + "-" + self.end_date.isoformat() + ")"

    def get_absolute_url(self):
        return reverse('relationartistartist_update', args=[str(self.id)])
