import binascii

from django.db import models
from django.urls import reverse

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

from regex import sub
from collections import Counter

from simple_history.models import HistoricalRecords


# Create your models here.
class GigFinder(models.Model):
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    api_key = models.CharField(max_length=500)
    history = HistoricalRecords()

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
        return RelationConcertArtist.objects.filter(artist=self).order_by('concert__id').distinct('concert__id').count()

    def concerts_in_countries(self):
        return Counter(RelationConcertArtist.objects.select_related('concert__relationconcertorganisation__organisation__location__country').filter(artist=self).exclude(concert__relationconcertorganisation__organisation__location__country__isnull=True).order_by('concert__id').distinct('concert__id').values_list('concert__relationconcertorganisation__organisation__location__country__name', flat=True)).most_common()

    def period(self):
        years = set()
        for relation_concert_artist in RelationConcertArtist.objects.select_related('concert').filter(artist=self):
            if relation_concert_artist.concert.date:
                years.add(relation_concert_artist.concert.date.year)
        return " and ".join([str(min(years)), str(max(years))]) if years else None

    def concerts(self):
        return set([rel.concert for rel in RelationConcertArtist.objects.filter(artist=self)])

    def recent_concerts(self, recent=5):
        return set([rel.concert for rel in RelationConcertArtist.objects.filter(artist=self).order_by('-concert__date').distinct()[:recent]])

    def organisations(self, top=5):
        orgs = []
        concerts = self.recent_concerts()
        for concert in concerts:
            for rel in concert.organisationsqs():
                orgs.append(rel.organisation)
        result = [o for o, b in Counter(orgs).most_common(top)]
        return result

    def find_similar_artists(self, top=5):
        related_artists = []
        for org in self.organisations():
            for artist in org.artists():
                if artist.pk != self.pk:
                    related_artists.append(artist)
        result = [a for a, b in Counter(related_artists).most_common(top)]
        return result

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

    def recently_confirmed(self):
        return abs(self.last_confirmed_by_musicbrainz.date() - datetime.now().date()) < timedelta(days=8)

    def recently_synchronized(self):
        return abs(self.last_synchronized.date() - datetime.now().date()) < timedelta(days=8)

    class Meta:
        ordering = ['-last_confirmed_by_musicbrainz', '-last_synchronized']


class ConcertAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    date = models.DateField()
    until_date = models.DateField(null=True, blank=True, default=None)
    is_festival = models.BooleanField(null=True, blank=True, default=None)
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
    cancelled = models.BooleanField(null=True, blank=True, default=False)
    history = HistoricalRecords()

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
        return timedelta(days=90) > (datetime.today().date() - self.last_seen_on)

    def maybe_deleted_or_cancelled(self):
        return self.date > self.last_seen_on

    def frequently_seen(self):
        return self.seen_count > 3

    def deleted(self):
        if self.gigfinder.name == "www.setlist.fm" and not self.recently_seen():
            return True
        elif self.ignore:
            return True
        return False

    def clean_location_from_assignments(self):
        loclist = [venue.organisation.location for venue in Venue.objects.select_related('organisation__location').filter(raw_location=self.raw_venue.raw_location).exclude(organisation=None)]
        if len(loclist) > 0:
            return Counter(loclist).most_common(1)[0][0]

    def clean_location_from_string(self):
        country = Country.objects.filter(name=self.raw_venue.raw_location.split("|")[-2]).first()
        location = Location.objects.filter(country=country).filter(city=self.raw_venue.raw_location.split("|")[-3]).first()
        return location

    def most_likely_clean_location(self):
        clean = self.raw_venue.organisation.location if self.raw_venue.organisation else None
        if clean is None:
            clean = self.clean_location_from_assignments()
            if clean is None:
                if not ("None|None" in self.raw_venue.raw_location or "||" in self.raw_venue.raw_location or self.raw_venue.non_assignable):
                    clean = self.clean_location_from_string()
        return clean

    def clean_loc_certainty(self):
        return self.clean_location_from_assignments() != self.clean_location_from_string()

    def save(self, *args, **kwargs):
        if not self.id:
            ca2c = ConcertannouncementToConcert(self)
            ca2c.automate()

        if self.id:
            self.seen_count += 1
            if self.concert and not self.concert.verified:
                self.concert.updated_at = datetime.now()
                self.concert.latitude = self.latitude
                self.concert.longitude = self.longitude
                self.concert.date = self.date if self.until_date is None else self.concert.date
                self.concert.until_date = self.until_date if self.concert.until_date is not None else None
                self.concert.cancelled = self.cancelled
                self.concert.save()
                if self.raw_venue.organisation and (self.raw_venue.organisation not in [rel.organisation for rel in self.concert.organisationsqs()]):
                    rel = RelationConcertOrganisation.objects.\
                        create(concert=self.concert,
                               organisation=self.raw_venue.organisation)
                    rel.save()
        super(ConcertAnnouncement, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-date']


class Venue(models.Model):
    raw_venue = models.CharField(max_length=200)
    raw_location = models.CharField(max_length=200, blank=True, null=True)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT, blank=True, null=True)
    non_assignable = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.raw_venue

    def clean_location(self):
        return self.organisation.location if self.organisation else None

    def location_estimated_from_raw_loc_string(self):
        country = Country.objects.filter(name=self.raw_location.split("|")[-2]).first()
        location = Location.objects.filter(country=country).filter(city=self.raw_location.split("|")[-3]).first()
        return location

    def location_estimated_from_venues_with_similar_raw_loc(self):
        loclist = [venue.organisation.location for venue in Venue.objects.select_related('organisation__location').filter(raw_location=self.raw_location).exclude(organisation=None)]
        if len(loclist) > 0:
            return Counter(loclist).most_common(1)[0][0]

    def get_absolute_url(self):
        return reverse('venue_detail', args=[str(self.id)])

    class Meta:
        ordering = ['raw_venue']


class Concert(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField(blank=True, null=True)
    until_date = models.DateField(blank=True, null=True, default=None)
    time = models.TimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False, blank=True, null=True)
    verified = models.BooleanField(default=False, blank=True, null=True)
    manual = models.BooleanField(default=False, blank=True, null=True)
    ignore = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genre = models.ManyToManyField("Genre", blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    annotation = models.CharField(max_length=500, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.artists() + " @ " + self.organisations() + " on " + self.date.isoformat()

    def is_ontologically_sound(self):
        concert_organisations = set([rel.organisation.pk for rel in self.organisationsqs()])
        concertannouncement_organisations = set([ca.raw_venue.organisation.pk if ca.raw_venue.organisation else -1 for ca in self.concertannouncements()])
        return concert_organisations == concertannouncement_organisations

    def artists(self):
        return ", ".join([rel.artist.name for rel in self.artistsqs() if rel.artist])

    def artistsqs(self):
        return RelationConcertArtist.objects.select_related('artist').filter(concert__id=self.id).order_by('artist__pk').distinct('artist')

    def organisations(self):
        return ", ".join([rel.organisation.name + " in "+ str(rel.organisation.location) for rel in self.organisationsqs() if rel.organisation])

    def organisationsqs(self):
        return RelationConcertOrganisation.objects.select_related('organisation__location__country').filter(concert__id=self.id).order_by('organisation__pk').distinct('organisation')

    def concertannouncements(self):
        return ConcertAnnouncement.objects.select_related('gigfinder').filter(concert=self)

    def is_upcoming(self):
        return self.date >= datetime.now().date() if self.date else True

    def is_new(self):
        return self.created_at.date() > (datetime.now() - timedelta(days=7)).date()

    def get_absolute_url(self):
        return reverse('concert_detail', args=[str(self.id)])

    def find_concurring_concerts(self):
        l = set()
        for this_org in RelationConcertOrganisation.objects.filter(concert__id=self.id):
            if this_org and this_org.organisation:
                l.add(this_org.organisation)
                l.update([r.organisation_b for r in this_org.organisation.organisationa.all()])
                l.update([r.organisation_a for r in this_org.organisation.organisationb.all()])
        return Concert.objects.filter(date=self.date).filter(relationconcertorganisation__organisation__in=l).exclude(id=self.id)

    def find_concerts_in_same_city_on_same_day(self):
        this_relation = RelationConcertOrganisation.objects.filter(concert__id=self.id).first()
        if this_relation and this_relation.organisation:
            if this_relation.organisation.location:
                this_location = this_relation.organisation.location
                extra_locations_a = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_b=this_location).values_list('location_a')]
                extra_locations_b = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_a=this_location).values_list('location_b')]
                locations = []
                locations.extend(extra_locations_a)
                locations.extend(extra_locations_b)
                locations.append(this_location.pk)
                return Concert.objects.filter(date=self.date).filter(relationconcertorganisation__organisation__location__pk__in=locations).exclude(id=self.id).distinct()

    def is_confirmed(self):
        for ca in ConcertAnnouncement.objects.filter(concert__id=self.id):
            if ca.recently_seen() or ca.frequently_seen():
                return True

    def delete(self):
        RelationConcertOrganisation.objects.filter(concert=self).all().delete()
        RelationConcertArtist.objects.filter(concert=self).all().delete()
        RelationConcertConcert.objects.filter(concert_a=self).all().delete()
        RelationConcertConcert.objects.filter(concert_b=self).all().delete()
        super(Concert, self).delete()

    def multiple_organisations_in_related_locations(self):
        locs = set([rel.organisation.location for rel in self.organisationsqs()])
        for loc_a in locs:
            for loc_b in locs:
                if loc_a.related_to(loc_b):
                    return True

    def get_changelist(self):
        changes = []
        for new_record in self.history.all():
            old_record = new_record.prev_record
            if old_record:
                delta = new_record.diff_against(old_record)
                if len(delta.changes) > 0:
                    changes.append(delta)
        return changes

    def get_organisations_changelist(self):
        changes = []
        for relation in RelationConcertOrganisation.history.filter(concert=self):
            if relation.history_type == "-":
                changes.append({"new_record": relation, "changes": [{"field": "organisation", "old": (relation.instance.organisation.pk, relation.instance.organisation.name), "new": ("deleted", "deleted")}]})
            if relation.history_type == "~":
                old_record = relation.prev_record
                if old_record:
                    delta = relation.diff_against(old_record)
                    deltachanges = []
                    for change in delta.changes:
                        field = change.field
                        old = (Organisation.objects.get(pk=change.old).pk, Organisation.objects.get(pk=change.old).name) if field == "organisation" else change.old
                        new = (Organisation.objects.get(pk=change.new).pk, Organisation.objects.get(pk=change.new).name) if field == "organisation" else change.new
                        deltachanges.append(
                            {
                                "field": field,
                                "old": old,
                                "new": new
                            }
                        )
                    delta.changes = deltachanges
                    changes.append(delta)
            if relation.history_type == "+":
                changes.append({"new_record": relation, "changes": [{"field": "organisation", "old": ("not existing", "not existing"), "new": (relation.instance.organisation.pk, relation.instance.organisation.name)}]})
        return changes

    def get_artists_changelist(self):
        changes = []
        for relation in RelationConcertArtist.history.filter(concert=self):
            if relation.history_type == "-":
                changes.append({"new_record": relation, "changes": [{"field": "artist", "old": (relation.instance.artist.pk, relation.instance.artist.name), "new": ("deleted", "deleted")}]})
            if relation.history_type == "~":
                old_record = relation.prev_record
                if old_record:
                    delta = relation.diff_against(old_record)
                    deltachanges = []
                    for change in delta.changes:
                        field = change.field
                        old = (Artist.objects.get(mbid=change.old).pk, Artist.objects.get(mbid=change.old).name) if field == "artist" else change.old
                        new = (Artist.objects.get(mbid=change.new).pk, Artist.objects.get(mbid=change.new).name) if field == "artist" else change.new
                        deltachanges.append(
                            {
                                "field": field,
                                "old": old,
                                "new": new
                            }
                        )
                    delta.changes = deltachanges
                    changes.append(delta)
            if relation.history_type == "+":
                changes.append({"new_record": relation, "changes": [{"field": "artist", "old": ("not existing", "not existing"), "new": (relation.instance.artist.pk, relation.instance.artist.name)}]})
        return changes

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
    sort_name = models.CharField(max_length=200)
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
        return self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else None

    def enddate(self):
        return self.end_date.strftime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else None

    def identifiersqs(self):
        return RelationOrganisationIdentifier.objects.select_related('identifier').filter(organisation=self)

    def concerts(self):
        return set([rel.concert for rel in RelationConcertOrganisation.objects.filter(organisation=self)])

    def recent_concerts(self, recent=5):
        return set([rel.concert for rel in RelationConcertOrganisation.objects.filter(organisation=self).order_by('-concert__date').distinct()[:recent]])

    def artists(self, top=5):
        artsts = set()
        for concert in self.recent_concerts():
            for rel in concert.artistsqs():
                artsts.add(rel.artist)
        result = [a for a, b in Counter(artsts).most_common(top)]
        return result

    def find_similar_organisations(self, top=5):
        related_organisations = []
        for artist in self.artists():
            for org in artist.organisations():
                if org.pk != self.pk:
                    related_organisations.append(org)
        result = [a for a, b in Counter(related_organisations).most_common(top)]
        return result

    class Meta:
        ordering = ['sort_name']


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
    disambiguation = models.CharField(max_length=200, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.city + \
               (" (" + self.zipcode + ")" if self.zipcode else "") + \
               (" [" + self.subcountry + "]" if self.subcountry and self.country.name != "Belgium" else "") + \
               (", " + self.country.name if self.country else ", No country")

    def related_to(self, other_location):
        return RelationLocationLocation.objects.filter(location_a=self).filter(location_b=other_location).exists() or RelationLocationLocation.objects.filter(location_a=other_location).filter(location_b=self).exists()

    def get_absolute_url(self):
        return reverse('location_detail', args=[str(self.id)])

    def get_changelist(self):
        changes = []
        for new_record in self.history.all():
            old_record = new_record.prev_record
            if old_record:
                delta = new_record.diff_against(old_record)
                changes.append(delta)
                for change in delta.changes:
                    print("{} changed from {} to {}".format(change.field, change.old, change.new))
        return changes

    class Meta:
        ordering = ['country', 'city']


class Country(models.Model):
    name = models.CharField(max_length=200)
    iso_code = models.CharField(max_length=2, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class RelationConcertArtist(models.Model):
    artist = models.ForeignKey("Artist", on_delete=models.PROTECT)
    artist_credited_as = models.CharField(max_length=200, blank=True, null=True)
    concert = models.ForeignKey("Concert", on_delete=models.PROTECT)
    relation_type = models.ManyToManyField("RelationConcertArtistType", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        try:
            return self.concert.title + " - " + self.artist.name
        except Exception as e:
            return str(e)

    def save(self, *args, **kwargs):
        super(RelationConcertArtist, self).save(*args, **kwargs)

    def previous_concert_by_artist(self):
        if self.concert.date:
            return RelationConcertArtist.objects.filter(artist=self.artist).filter(concert__date__lt=self.concert.date).order_by('-concert__date').first()

    def next_concert_by_artist(self):
        if self.concert.date:
            return RelationConcertArtist.objects.filter(artist=self.artist).filter(concert__date__gt=self.concert.date).order_by('concert__date').first()

    def simultaneous_concerts_by_artist(self):
        if self.concert.date:
            return RelationConcertArtist.objects.filter(artist=self.artist).filter(concert__date=self.concert.date).exclude(concert__id=self.concert.id)

    class Meta:
        ordering = ['concert']


class RelationConcertArtistType(models.Model):
    name = models.CharField(max_length=200)
    history = HistoricalRecords()

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
        try:
            return self.concert.title + " " + (self.organisation_credited_as + " (" + self.organisation.name + ")" if self.organisation_credited_as else str(self.organisation))
        except Exception as e:
            return str(e)

    def save(self, *args, **kwargs):
        super(RelationConcertOrganisation, self).save(*args, **kwargs)

    def previous_concert_at_organisation(self):
        if self.concert.date:
            return RelationConcertOrganisation.objects.filter(organisation=self.organisation).filter(concert__date__lt=self.concert.date).order_by('-concert__date').first()

    #TODO def concert of same artist on same day

    def next_concert_at_organisation(self):
        if self.concert.date:
            return RelationConcertOrganisation.objects.filter(organisation=self.organisation).filter(concert__date__gt=self.concert.date).order_by('concert__date').first()

    class Meta:
        ordering = ['concert']


class RelationConcertOrganisationType(models.Model):
    name = models.CharField(max_length=200)
    history = HistoricalRecords()

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
    history = HistoricalRecords()

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
    history = HistoricalRecords()

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

    def merge(self, *args, **kwargs):
        mmi = MergedModelInstance.create(self.primary_object, [ao for ao in self.alias_objects.all()], keep_old=False)

    def get_absolute_url(self):
        return reverse('concertsmerge_confirm', args=[str(self.id)])

    class Meta:
        ordering = ['primary_object']


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
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class RelationConcertConcert(models.Model):
    concert_a = models.ForeignKey("Concert", on_delete=models.PROTECT, related_name='concerta')
    concert_b = models.ForeignKey("Concert", on_delete=models.PROTECT, related_name='concertb')
    relation_type = models.ManyToManyField("RelationConcertConcertType", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.concert_a.title + " " + self.relation_type + " " + self.concert_b.title

    def get_absolute_url(self):
        return reverse('relationconcertconcert_update', args=[str(self.id)])


class RelationConcertConcertType(models.Model):
    name = models.CharField(max_length=200)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class RelationLocationLocation(models.Model):
    location_a = models.ForeignKey("Location", on_delete=models.PROTECT, related_name='locationa')
    location_b = models.ForeignKey("Location", on_delete=models.PROTECT, related_name='locationb')
    relation_type = models.ManyToManyField("RelationLocationLocationType", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.location_a) + " " + self.relation_type + " " + str(self.location_b)

    def get_absolute_url(self):
        return reverse('relationlocationlocation_update', args=[str(self.id)])


class RelationLocationLocationType(models.Model):
    name = models.CharField(max_length=200)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ExternalIdentifierService(models.Model):
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ExternalIdentifier(models.Model):
    identifier = models.CharField(max_length=200)
    service = models.ForeignKey("ExternalIdentifierService", on_delete=models.PROTECT, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.identifier + " (" + (self.service.name if self.service else "No service provided") + ")"


class RelationOrganisationIdentifier(models.Model):
    YEAR = 2
    MONTH = 5
    DAY = 8
    PRECISION = (
        (YEAR, 'Precise up to the year'),
        (MONTH, 'Precise up to the month'),
        (DAY, 'Precise up to the day')
    )
    start_date = models.DateField(blank=True, null=True)
    start_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    end_date = models.DateField(blank=True, null=True)
    end_date_precision = models.PositiveSmallIntegerField(choices=PRECISION, default=YEAR)
    organisation = models.ForeignKey("Organisation", on_delete=models.PROTECT)
    identifier = models.ForeignKey("ExternalIdentifier", on_delete=models.PROTECT)
    history = HistoricalRecords()

    def __str__(self):
        startdate = self.start_date.strptime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"
        enddate = self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"
        return self.organisation.name + " " + self.identifier.identifier + " (" + self.identifier.service.name + ")" + " (" + startdate + "-" + enddate + ")"

    def startdate(self):
        return self.start_date.strftime("%Y/%m/%d"[0:self.start_date_precision]) if self.start_date else "?"

    def enddate(self):
        return self.end_date.strptime("%Y/%m/%d"[0:self.end_date_precision]) if self.end_date else "?"

    def get_absolute_url(self):
        return reverse('relationorganisationidentifier_update', args=[str(self.id)])


class ConcertannouncementToConcert:
    def __init__(self, concertannouncement):
        self.concertannouncement = concertannouncement
        self.masterconcert = None
        most_likely_clean_location = self.concertannouncement.most_likely_clean_location()
        extra_locations_a = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_b=most_likely_clean_location).values_list('location_a')]
        extra_locations_b = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_a=most_likely_clean_location).values_list('location_b')]
        self.locations = []
        self.locations.extend(extra_locations_a)
        self.locations.extend(extra_locations_b)
        if most_likely_clean_location:
            self.locations.append(most_likely_clean_location.pk)

    def automate(self):
        print("working on", self.concertannouncement, self.concertannouncement.pk)

        if self._concertannouncement_has_daterange():
            print("\tCA with date range")
            self.masterconcert = self._exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist()
            if self.masterconcert:
                print("\t\tfound a MC to relate to")
                self._relate_concertannouncement_to_masterconcert()
                if self._venue_is_not_related_to_organisation():
                    print("\t\t\tvenue has no organisation, so creating one")
                    self._create_new_unverified_organisation_and_relate_to_venue()
                if self._is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert():
                    print("\t\t\tattach the organisation of the venue to the concert")
                    self._relate_organisation_related_to_venue_also_to_the_masterconcert()
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

    def _concertannouncement_has_daterange(self):
        return self.concertannouncement.date < self.concertannouncement.until_date if self.concertannouncement.until_date else False

    def venue_organisation_is_in_concert_related_organisation(self):
        orgs = set(RelationConcertOrganisation.objects.filter(concert=self.concertannouncement.concert).values_list("organisation", flat=True))
        return self.concertannouncement.raw_venue.organisation.pk in orgs

    def _exists_non_cancelled_masterconcert_within_daterange_in_location_with_artist(self):
        locations = [self.concertannouncement.most_likely_clean_location()]
        extra_locations_a = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_b=locations[0]).values_list('location_a')]
        extra_locations_b = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_a=locations[0]).values_list('location_b')]
        locations.append(extra_locations_a)
        locations.append(extra_locations_b)
        period_concert = Concert.objects.\
            filter(until_date__isnull=False).\
            filter(date__lte=self.concertannouncement.date).\
            filter(until_date__gte=self.concertannouncement.until_date).\
            exclude(ignore=True).\
            exclude(cancelled=True).\
            filter(relationconcertartist__artist=self.concertannouncement.artist).\
            filter(relationconcertorganisation__organisation__location__pk__in=self.locations)
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
                filter(relationconcertorganisation__organisation__location__pk__in=self.locations)
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
            filter(relationconcertorganisation__organisation__location__pk__in=self.locations)
        if period_concert:
            return period_concert.first()
        else:
            specific_concert = Concert.objects.\
                filter(until_date__isnull=True).\
                filter(date=self.concertannouncement.date).\
                exclude(ignore=True).\
                exclude(cancelled=True).\
                filter(relationconcertartist__artist=self.concertannouncement.artist).\
                filter(relationconcertorganisation__organisation__location__pk__in=self.locations)
            if specific_concert:
                return specific_concert.first()
            else:
                return None

    def _is_venue_related_to_organisation_other_than_organisations_already_related_to_masterconcert(self):
        return self.concertannouncement.raw_venue.organisation not in [rel.organisation for rel in self.masterconcert.organisationsqs()]

    def _relate_concertannouncement_to_masterconcert(self):
        self.concertannouncement.concert = self.masterconcert

    def _perhaps_specify_masterconcert_date(self):
        if self.concertannouncement.concert.until_date:
            print("----specifying masterconcert date")
            self.concertannouncement.concert.date = self.concertannouncement.date
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
        return (not self.concertannouncement.raw_venue.non_assignable) and (self.concertannouncement.raw_venue.organisation is None)

    def _create_new_unverified_organisation_and_relate_to_venue(self):
        # what is the most likely location of the venue
        # is there an organisation in that location that is similar to the raw_venue
        # if there is, relate that organisation to venue
        # if not, create new organisation
        try:
            stad, land, bron = self.concertannouncement.raw_venue.raw_venue.split("|")[-3:]
            name_prop = "|".join(self.concertannouncement.raw_venue.raw_venue.split("|")[:-3])
            name = name_prop if len(name_prop.strip()) > 0 else self.concertannouncement.raw_venue.raw_venue

            try:
                year = int(name[-4:])
                if name[-5] == " " and (1950 < year < 2055):
                    name = sub("\d\d\d\d$", "", name)
                    name.strip()
            except ValueError:
                pass

            loc = None
            org = None
            if land.lower() != "none" or stad.lower() != "none" or land != "" or stad != "":
                if name not in ("None", "nan"):
                    loc = self.concertannouncement.most_likely_clean_location()
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
                   until_date=(self.concertannouncement.until_date if self.concertannouncement.until_date != self.concertannouncement.date else None),
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
