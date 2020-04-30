import binascii

from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords

from django_super_deduper.merge import MergedModelInstance

from json import dumps
import hashlib
import hmac

from requests import post
from datetime import datetime, timedelta, date
import pytz
from math import sqrt
import os
from collections import Counter


# Create your models here.
class GigFinder(models.Model):
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    api_key = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=200)
    disambiguation = models.CharField(max_length=200, blank=True, null=True)
    mbid = models.CharField(max_length=50, primary_key=True)
    include = models.BooleanField(default=False)
    exclude = models.BooleanField(default=False)
    genre = models.ManyToManyField("Genre", blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('artist_detail', args=[str(self.mbid)])

    def concert_count(self):
        return RelationConcertArtist.objects.filter(artist=self).count()

    def concerts_in_countries(self):
        locations = set()
        for relation_concert_artist in RelationConcertArtist.objects.filter(artist=self):
            for relation_concert_organisation in RelationConcertOrganisation.objects.filter(concert=relation_concert_artist.concert):
                if relation_concert_organisation.organisation:
                    locations.add(relation_concert_organisation.organisation.location)
        return len(set([loc.country for loc in locations if loc]))

    def period(self):
        years = set()
        for relation_concert_artist in RelationConcertArtist.objects.filter(artist=self):
            years.add(relation_concert_artist.concert.date.year)
        return "-".join([str(min(years)), str(max(years))]) if years else None

    def concerts(self):
        return [rel.concert for rel in RelationConcertArtist.objects.filter(artist=self)]

    class Meta:
        ordering = ['name']


class GigFinderUrl(models.Model):
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    gigfinder = models.ForeignKey("GigFinder", on_delete=models.PROTECT)
    url = models.URLField()
    last_confirmed_by_musicbrainz = models.DateTimeField(default=datetime(1970, 1, 1, 0, 0, 0))
    last_synchronized = models.DateTimeField(default=datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc))

    def __str__(self):
        return self.url + " (" + str(self.artist) + ", " + str(self.gigfinder) + ")"

    class Meta:
        ordering = ['-last_confirmed_by_musicbrainz', '-last_synchronized']


class ConcertAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    gigfinder = models.ForeignKey("GigFinder", on_delete=models.PROTECT)
    gigfinder_concert_id = models.CharField(max_length=250, blank=True, null=True)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT, blank=True, null=True)
    last_seen_on = models.DateField(auto_now=True)
    seen_count = models.IntegerField(default=1)
    raw_venue = models.ForeignKey("Venue", on_delete=models.PROTECT, blank=True, null=True)
    ignore = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('concertannouncement_detail', args=[str(self.id)])

    def far_from_concert(self):
        x1 = self.concert.latitude
        x2 = self.latitude
        y1 = self.concert.longitude
        y2 = self.longitude
        try:
            dist = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        except TypeError:
            dist = 0
        return dist > 0.01

    def recently_seen(self):
        return timedelta(days=30) > (datetime.today().date() - self.last_seen_on)

    def frequently_seen(self):
        return self.seen_count > 3

    def deleted(self):
        if self.gigfinder.name == "www.setlist.fm" and not self.recently_seen():
            return True
        elif self.ignore:
            return True
        return False

    def most_likely_clean_location(self):
        if not "None|None" in self.raw_venue.raw_location:
            loclist = [venue.organisation.location for venue in Venue.objects.filter(raw_location=self.raw_venue.raw_location).exclude(organisation=None)]
            if len(loclist) > 0:
                return Counter(loclist).most_common(1)[0][0]
            else:
                country = Country.objects.filter(name=self.raw_venue.raw_location.split("|")[-2]).first()
                location = Location.objects.filter(country=country).filter(city=self.raw_venue.raw_location.split("|")[-3]).first()
                return location

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
        if self.id:
            self.seen_count += 1
            if self.concert and not self.concert.verified:
                self.concert.updated_at = datetime.now()
                self.concert.latitude = self.latitude
                self.concert.longitude = self.longitude
                self.concert.save()
        super(ConcertAnnouncement, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-date']

    def _exists_non_cancelled_masterconcert_on_date_with_artist(self):
        try:
            return Concert.objects.filter(date=self.date).exclude(ignore=True).exclude(cancelled=True).filter(relationconcertartist__artist=self.artist).filter(relationconcertorganisation__organisation__location=self.most_likely_clean_location()).first()
        except IndexError:
            return None

    def _is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self):
        masterconcert_organisations = [rel.organisation for rel in RelationConcertOrganisation.objects.filter(concert=self.masterconcert)]
        return self.raw_venue.organisation and self.raw_venue.organisation not in masterconcert_organisations

    def _relate_concertannouncement_to_masterconcert(self):
        self.concert = self.masterconcert

    def _relate_organisation_related_to_venue_also_to_the_masterconcert(self):
        rco = RelationConcertOrganisation.objects.create(concert=self.masterconcert, organisation=self.raw_venue.organisation, verified=False)
        rco.save()

    def _relate_organisation_related_to_masterconcert_to_venue(self):
        org = RelationConcertOrganisation.objects.filter(concert=self.masterconcert)[0].organisation  # TODO what if several organisations connected to masterconcert?
        self.raw_venue.organisation = org
        self.raw_venue.save()

    def _venue_is_not_related_to_organisation(self):
        return self.raw_venue.organisation is None

    def _create_new_unverified_organisation_and_relate_to_venue(self):
        name_prop, stad, land, bron, *rest = self.raw_venue.raw_venue.split("|")
        name = name_prop if len(name_prop.strip()) > 0 else self.raw_venue.raw_venue
        country = Country.objects.filter(name=land).first()
        if not country:
            country = Country.objects.filter(iso_code=land.lower()).first()
        loc = Location.objects.filter(city__istartswith=stad).filter(country=country).first()
        org = Organisation.objects.create(name=name,
                                          annotation=(stad if len(stad.strip()) > 0 else "unknown city") + ", " + (land if len(land.strip()) else "unknown country") + " (" + bron + ")",
                                          location=loc, verified=False)
        org.save()
        self.raw_venue.organisation = org
        self.raw_venue.save()

    def _create_new_masterconcert_with_concertannouncement_organisation_artist(self):
        mc = Concert.objects.create(title=self.title, date=self.date, latitude=self.latitude, longitude=self.longitude)
        mc.save()
        for genre in self.artist.genre.all():
            mc.genre.add(genre)
        mc.save()
        relco = RelationConcertOrganisation(concert=mc, organisation=self.raw_venue.organisation, verified=False)
        relco.save()
        relca = RelationConcertArtist(concert=mc, artist=self.artist)
        relca.save()
        self.concert = mc


class Venue(models.Model):
    raw_venue = models.CharField(max_length=200)
    raw_location = models.CharField(max_length=200, blank=True, null=True)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT, blank=True, null=True)
    non_assignable = models.BooleanField(default=False)

    def __str__(self):
        return self.raw_venue

    def clean_location(self):
        return self.organisation.location if self.organisation else None

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
    ignore = models.BooleanField(default=False, blank=True, null=True)
    history = HistoricalRecords()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genre = models.ManyToManyField("Genre", blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    annotation = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

    def artists(self):
        return ", ".join([rel.artist.name for rel in RelationConcertArtist.objects.filter(concert__id=self.id)])

    def organisations(self):
        return ", ".join([rel.organisation.name for rel in RelationConcertOrganisation.objects.filter(concert__id=self.id) if rel.organisation])

    def is_upcoming(self):
        return self.date >= datetime.now().date() if self.date else True

    def is_new(self):
        return self.created_at.date() > (datetime.now() - timedelta(days=7)).date()

    def get_absolute_url(self):
        return reverse('concert_detail', args=[str(self.id)])

    def find_concurring_concerts(self):
        this_org = RelationConcertOrganisation.objects.filter(concert__id=self.id).first()
        if this_org and this_org.organisation:
            return Concert.objects.filter(date=self.date).filter(relationconcertorganisation__organisation=this_org.organisation).exclude(id=self.id)

    def is_confirmed(self):
        for ca in ConcertAnnouncement.objects.filter(concert__id=self.id):
            if ca.recently_seen() or ca.frequently_seen():
                return True

    def save(self, *args, **kwargs):
        send = False
        if self.id and send:
            rel_artiest = RelationConcertArtist.objects.filter(concert=self).first()
            rel_organisation = RelationConcertOrganisation.objects.filter(concert=self).first()
            data = {
                "event_id": str(self.id),
                "titel": self.title,
                "titel_generated": self.title,
                "datum": self.date.strftime("%Y/%m/%d") if isinstance(self.date, date) else self.date.replace("-", "/") if self.date else None,
                "artiest": rel_artiest.artist.name if rel_artiest else None,
                "artiest_merge_naam": rel_artiest.artist.name if rel_artiest else None,
                "artiest_mb_id": rel_artiest.artist.mbid if rel_artiest else None,
                "cancelled": self.cancelled,
                "ignore": self.ignore,
                "latitude": self.latitude,
                "longitude": self.longitude
            }

            if rel_organisation:
                if rel_organisation.organisation:
                    if rel_organisation.organisation.location:
                        data["stad_clean"] = rel_organisation.organisation.location.city
                        data["land_clean"] = rel_organisation.organisation.location.country.name if rel_organisation.organisation.location.country else None
                        data["iso_code_clean"] = rel_organisation.organisation.location.country.iso_code if rel_organisation.organisation.location.country else None
                    data["venue_clean"] = rel_organisation.organisation.name

            for i, ca in enumerate(ConcertAnnouncement.objects.filter(concert=self)):
                source = ca.gigfinder.name
                source_link = str(ca.gigfinder.base_url) + str(ca.gigfinder_concert_id)
                data["source_" + str(i)] = source
                data["source_link_" + str(i)] = source_link

            message = bytes(dumps(data), "utf-8")

            print(message)

            try:
                with open("hlwtadmin/mrhenrysecret.txt", "rb") as f:
                    secret = bytes(f.read().strip())
            except FileNotFoundError:
                secret = bytes(os.environ.get('MR_HENRY_API_KEY').strip("'"), "utf-8")

            signature = binascii.b2a_hex(hmac.new(secret, message, digestmod=hashlib.sha256).digest())

            base_url = "https://have-love-will-travel.herokuapp.com/"
            url = base_url + "import-json"

            params = {"signature": signature, "test": "test" in args}
            headers = {"Content-Type": "application/json"}

            r = None
            try:
                r = post(url, data=message, params=params, headers=headers)
                if r.status_code != 200:
                    print("issue with sending this record to the api", message, r.status_code, r.headers, r.content)
            except Exception as e:
                print(e)
        super(Concert, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-date']


class Organisation(models.Model):
    YEAR = 2
    MONTH = 5
    DAY = 8
    PRECISION = (
        (YEAR, 'Precise up to the year'),
        (MONTH, 'Precise up to the month'),
        (DAY, 'Precise up to the day')
    )
    name = models.CharField(max_length=200)
    disambiguation = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.PROTECT, blank=True, null=True)
    organisation_type = models.ManyToManyField("OrganisationType", blank=True)
    start_date = models.DateField(blank=True, null=True)
    start_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    end_date = models.DateField(blank=True, null=True)
    end_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    website = models.URLField(blank=True, null=True)
    verified = models.BooleanField(default=False, blank=True, null=True)
    genre = models.ManyToManyField("Genre", blank=True)
    active = models.BooleanField(blank=True, null=True)
    capacity = models.CharField(max_length=250, null=True, blank=True)
    annotation = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organisation_detail', args=[str(self.id)])

    def startdate(self):
        return self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"

    def enddate(self):
        return self.end_date.strftime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"

    class Meta:
        ordering = ['name']


class OrganisationType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Location(models.Model):
    city = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    country = models.ForeignKey("Country", blank=True, null=True, on_delete=models.PROTECT)
    subcountry = models.CharField(max_length=200, blank=True, null=True)
    verified = models.BooleanField(blank=True, null=True, default=True)

    def __str__(self):
        return self.city + \
               (" (" + self.zipcode + ")" if self.zipcode else "") + \
               (" [" + self.subcountry + "]" if self.subcountry and self.country.name != "Belgium" else "") + \
               (", " + self.country.name if self.country else ", No country")

    def get_absolute_url(self):
        return reverse('location_detail', args=[str(self.id)])

    class Meta:
        ordering = ['country', 'city']


class Country(models.Model):
    name = models.CharField(max_length=200)
    iso_code = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class RelationConcertArtist(models.Model):
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    artist_credited_as = models.CharField(max_length=200, blank=True, null=True)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)
    history = HistoricalRecords()
    relation_type = models.ManyToManyField("RelationConcertArtistType", blank=True)

    def __str__(self):
        return self.concert.title + " - " + self.artist.name

    def save(self, *args, **kwargs):
        super(RelationConcertArtist, self).save(*args, **kwargs)
        self.concert.save()

    def previous_concert_by_artist(self):
        if self.concert.date:
            return RelationConcertArtist.objects.filter(artist=self.artist).filter(concert__date__lt=self.concert.date).order_by('-concert__date').first()

    def next_concert_by_artist(self):
        if self.concert.date:
            return RelationConcertArtist.objects.filter(artist=self.artist).filter(concert__date__gt=self.concert.date).order_by('concert__date').first()

    class Meta:
        ordering = ['concert']


class RelationConcertArtistType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationConcertOrganisation(models.Model):
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT, blank=True, null=True)
    organisation_credited_as = models.CharField(max_length=200, blank=True, null=True)
    relation_type = models.ManyToManyField("RelationConcertOrganisationType", blank=True)
    verified = models.BooleanField(blank=True, default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.concert.title + " " + (self.organisation_credited_as + " (" + self.organisation.name + ")" if self.organisation_credited_as else str(self.organisation))

    def save(self, *args, **kwargs):
        super(RelationConcertOrganisation, self).save(*args, **kwargs)
        self.concert.save()

    def previous_concert_at_organisation(self):
        if self.concert.date:
            return RelationConcertOrganisation.objects.filter(organisation=self.organisation).filter(concert__date__lt=self.concert.date).order_by('-concert__date').first()

    def next_concert_at_organisation(self):
        if self.concert.date:
            return RelationConcertOrganisation.objects.filter(organisation=self.organisation).filter(concert__date__gt=self.concert.date).order_by('concert__date').first()

    class Meta:
        ordering = ['concert']


class RelationConcertOrganisationType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationOrganisationOrganisation(models.Model):
    YEAR = 2
    MONTH = 5
    DAY = 8
    PRECISION = (
        (YEAR, 'Precise up to the year'),
        (MONTH, 'Precise up to the month'),
        (DAY, 'Precise up to the day')
    )
    organisation_a = models.ForeignKey("Organisation", on_delete=models.PROTECT, related_name='organisationa')
    organisation_b = models.ForeignKey("Organisation", on_delete=models.PROTECT, related_name='organisationb')
    start_date = models.DateField(blank=True, null=True)
    start_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    end_date = models.DateField(blank=True, null=True)
    end_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    relation_type = models.ManyToManyField("RelationOrganisationOrganisationType", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        startdate = self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"
        enddate = self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"
        return self.organisation_a.name + " " + self.relation_type + " " + self.organisation_b.name + " (" + startdate + "-" + enddate + ")"

    def startdate(self):
        return self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"

    def enddate(self):
        return self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"

    def get_absolute_url(self):
        return reverse('relationorganisationorganisation_update', args=[str(self.id)])


class RelationOrganisationOrganisationType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationArtistArtist(models.Model):
    YEAR = 2
    MONTH = 5
    DAY = 8
    PRECISION = (
        (YEAR, 'Precise up to the year'),
        (MONTH, 'Precise up to the month'),
        (DAY, 'Precise up to the day')
    )
    artist_a = models.ForeignKey("Artist", on_delete=models.PROTECT, related_name='artista')
    artist_b = models.ForeignKey("Artist", on_delete=models.PROTECT, related_name='artistb')
    start_date = models.DateField(blank=True, null=True)
    start_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    end_date = models.DateField(blank=True, null=True)
    end_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    relation_type = models.ManyToManyField("RelationArtistArtistType", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        startdate = self.start_date.strptime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"
        enddate = self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"
        return self.artist_a.name + " " + self.relation_type + " " + self.artist_b.name + " (" + startdate + "-" + enddate + ")"

    def startdate(self):
        return self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"

    def enddate(self):
        return self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"

    def get_absolute_url(self):
        return reverse('relationartistartist_update', args=[str(self.id)])


class RelationArtistArtistType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class OrganisationsMerge(models.Model):
    primary_object = models.ForeignKey("Organisation", on_delete=models.PROTECT, related_name="primary")
    alias_objects = models.ManyToManyField("Organisation", related_name="aliases")

    def __str__(self):
        return self.primary_object.name + " < " + ", ".join([str(ao.name) for ao in self.alias_objects.all()])

    def delete(self, *args, **kwargs):
        mmi = MergedModelInstance.create(self.primary_object, [ao for ao in self.alias_objects.all()], keep_old=False)
        super(OrganisationsMerge, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('organisationsmerge_delete', args=[str(self.id)])


class ConcertsMerge(models.Model):
    primary_object = models.ForeignKey("Concert", on_delete=models.PROTECT, related_name="primary")
    alias_objects = models.ManyToManyField("Concert", related_name="aliases")

    def __str__(self):
        return self.primary_object.title + " < " + ", ".join([str(ao.title) for ao in self.alias_objects.all()])

    def delete(self, *args, **kwargs):
        mmi = MergedModelInstance.create(self.primary_object, [ao for ao in self.alias_objects.all()], keep_old=False)
        super(ConcertsMerge, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('concertsmerge_delete', args=[str(self.id)])


class LocationsMerge(models.Model):
    primary_object = models.ForeignKey("Location", on_delete=models.PROTECT, related_name="primary")
    alias_objects = models.ManyToManyField("Location", related_name="aliases")

    def __str__(self):
        return str(self.primary_object) + " < " + ", ".join([str(ao) for ao in self.alias_objects.all()])

    def delete(self, *args, **kwargs):
        mmi = MergedModelInstance.create(self.primary_object, [ao for ao in self.alias_objects.all()], keep_old=False)
        super(LocationsMerge, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('locationsmerge_delete', args=[str(self.id)])


class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RelationConcertConcert(models.Model):
    concert_a = models.ForeignKey("Concert", on_delete=models.PROTECT, related_name='concerta')
    concert_b = models.ForeignKey("Concert", on_delete=models.PROTECT, related_name='concertb')
    relation_type = models.ManyToManyField("RelationConcertConcertType", blank=True)

    def __str__(self):
        return self.concert_a.title + " " + self.relation_type + " " + self.concert_b.title

    def get_absolute_url(self):
        return reverse('relationconcertconcert_update', args=[str(self.id)])


class RelationConcertConcertType(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
