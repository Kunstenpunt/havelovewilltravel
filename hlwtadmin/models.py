from django.db import models
from django.urls import reverse

# Create your models here.


class Musicbrainz(models.Model):
    name = models.CharField(max_length=200)
    mbid = models.CharField(max_length=25)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('artist_detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']


class GigfinderUrl(models.Model):
    url = models.URLField()
    gigfinder = models.ForeignKey("Gigfinder", on_delete=models.PROTECT)
    musicbrainz = models.ForeignKey("Musicbrainz", on_delete=models.PROTECT)


class Gigfinder(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class ConcertAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    musicbrainz = models.ForeignKey("Musicbrainz", on_delete=models.PROTECT)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    gigfinder = models.ForeignKey("Gigfinder", on_delete=models.PROTECT)
    gigfinder_artist_name = models.CharField(max_length=200)
    gigfinder_concert_id = models.CharField(max_length=200)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT, blank=True, null=True)
    last_seen_on = models.DateField(auto_now=True) # TODO dat klopt niet
    raw_venue = models.ForeignKey("RawVenue", on_delete=models.PROTECT, blank=True, null=True)
    ignore = models.BooleanField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('concertannouncement_detail', args=[str(self.id)])

    class Meta:
        ordering = ['-date']


class RawVenue(models.Model):
    raw_venue = models.CharField(max_length=200)
    venue = models.ForeignKey("Organity", on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return self.raw_venue

    def get_absolute_url(self):
        return reverse('rawvenue_detail', args=[str(self.id)])

    class Meta:
        ordering = ['raw_venue']


class Concert(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('concert_detail', args=[str(self.id)])

    class Meta:
        ordering = ['-date']


class Organity(models.Model):
    name = models.CharField(max_length=200)
    address = models.ForeignKey("Address", on_delete=models.PROTECT)
    organity_type = models.ManyToManyField("OrganityType")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organity_detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']


class OrganityType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Address(models.Model):
    address = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.PROTECT)

    def __str__(self):
        return str(self.address) + ", " + str(self.location)

    class Meta:
        ordering = ['address', 'location']


class Location(models.Model):
    city = models.CharField(max_length=200)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    country = models.ForeignKey("Country", on_delete=models.PROTECT)

    def __str__(self):
        return self.city + ", " + self.country.name


class Country(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationConcertMusicbrainz(models.Model):
    musicbrainz = models.ForeignKey("Musicbrainz", on_delete=models.PROTECT)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)

    def __str__(self):
        return self.concert.title + " - " + self.musicbrainz.name


class RelationConcertOrganity(models.Model):
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)
    organity = models.ForeignKey("Organity", on_delete=models.PROTECT)
    organity_credited_as = models.CharField(max_length=200)
    relation_type = models.ManyToManyField("RelationConcertOrganityType")

    def __str__(self):
        return self.concert.title + " " + self.organity_credited_as + " (" + self.organity.name + ")"


class RelationConcertOrganityType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationOrganityOrganity(models.Model):
    entity_a = models.ForeignKey("Organity", on_delete=models.PROTECT, related_name='organitya')
    entity_b = models.ForeignKey("Organity", on_delete=models.PROTECT, related_name='organityb')
    start_date = models.DateField()
    end_date = models.DateField()
    relation_type = models.CharField(max_length=200)

    def __str__(self):
        return self.entity_a.name + " " + self.relation_type + " " + self.entity_b.name + " (" + self.start_date.isoformat() + "-" + self.end_date.isoformat() + ")"
