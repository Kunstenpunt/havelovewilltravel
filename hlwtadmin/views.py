from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django import forms
from dal import autocomplete
from django.db.models import Q, Exists, Count, F, Max, DateField
from django.db.models.functions import Length
from django.utils.html import format_html

from django.core.paginator import Paginator

from datetime import datetime, timedelta

from django.views.generic.list import MultipleObjectMixin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, RelationConcertConcert, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, \
    RelationArtistArtist, OrganisationsMerge, ConcertsMerge, LocationsMerge, GigFinderUrl, RelationOrganisationIdentifier, \
    ExternalIdentifier, RelationLocationLocation, RelationLocationLocationType


class SubcountryAutocompleteFromList(autocomplete.Select2ListView):
    def get_list(self):
        qs = Location.objects.all()

        country = self.forwarded.get('country', None)

        if country:
            qs = qs.filter(country=country)

        if self.q:
            qs = qs.filter(subcountry__unaccent__iregex=self.q)
        return set(qs.values_list("subcountry", flat=True))


class ConcertAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Concert.objects.all()

        first_selected = self.forwarded.get('primary_object', None)
        artist = self.forwarded.get('artist', None)

        if artist:
            qs = qs.filter(relationconcertartist__artist__mbid=artist)

        if first_selected:
            qs = qs.exclude(id=first_selected)

        if self.q:
            qs = qs.filter(title__unaccent__iregex=self.q)
        return qs

    def get_result_label(self, item):
        return format_html('<div style="overflow: auto;"><div style="float: left;"><i>{}</i><br><b>{}</b> by <b>{}</b> at <b>{}</b></div><div align="right" style="overflow: hidden;"><a target="_blank" href="{}">ctrl+click to open</a></div></div>',
                           item.title[0:80],
                           (item.date.isoformat() if item.date else "No date"),
                           item.artists()[0:35],
                           item.organisations()[0:45],
                           item.get_absolute_url()
                           )


class ConcertAnnouncementAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ConcertAnnouncement.objects.all()
        if self.q:
            qs = qs.filter(title__unaccent__iregex=self.q)
        return qs


class IdentifierAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ExternalIdentifier.objects.all()
        if self.q:
            qs = qs.filter(identifier__istartswith=self.q)
        return qs


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Artist.objects.all()
        if self.q:
            qs = qs.filter(name__unaccent__iregex=self.q)
        return qs

    def get_result_label(self, item):
        return format_html('{} <i>{}</i> -- <a target="_blank" href="{}">ctrl+click to open</a>', item.name, (item.disambiguation if item.disambiguation else "No disambiguation"), item.get_absolute_url())


class OrganisationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organisation.objects.all()

        first_selected = self.forwarded.get('primary_object', None)
        location = self.forwarded.get('location', None)

        if location:
            qs = qs.filter(location__id=location)

        if first_selected:
            qs = qs.exclude(id=first_selected)

        if self.q:
            qs = qs.filter(name__unaccent__iregex=self.q)
        return qs

    def get_result_label(self, item):
        return format_html(
            '<div style="overflow: auto;"><div style="float: left;">{} <i>{}</i><br><b>{}</b>{} <img title="{}" style="width: 16px; height: 16px; border: 0px; margin-left: 1px; margin-right: 1px;" src="{}{}.png" /></div><div align="right" style="overflow: hidden;"><a target="_blank" href="{}">ctrl+click to open</a></div></div>',
            item.name[0:80],
            (item.disambiguation if item.disambiguation else "No disambiguation"),
            (item.location if item.location else "No location"),
            "",
            (item.location.country if (item.location and item.location.country) else "No country"),
            "/static/flags/",
            (item.location.country.iso_code if (item.location and item.location.country) else None),
            item.get_absolute_url()
            )


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Location.objects.all()

        first_selected = self.forwarded.get('primary_object', None)
        country = self.forwarded.get('country', None)

        if country:
            qs = qs.filter(country__id=country)

        if first_selected:
            qs = qs.exclude(id=first_selected)

        if self.q:
            #qs = qs.filter(Q(city__unaccent__iregex=self.q) | Q(country__name__unaccent__iregex=self.q))
            qs = qs.filter(city__unaccent__iregex=self.q)
        return qs


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Country.objects.all()
        if self.q:
            qs = qs.filter(name__unaccent__iregex=self.q)
        return qs


class VenueAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Venue.objects.all()
        if self.q:
            qs = qs.filter(raw_venue__unaccent__iregex=self.q)
        return qs


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    context = {
        'num_concerts': Concert.objects.count(),
        'num_artists': Artist.objects.count(),
        'num_organisations': Organisation.objects.count(),
        'num_venues': Venue.objects.count(),
        'num_announcements': ConcertAnnouncement.objects.count(),
        'num_locations': Location.objects.count(),
        'num_excluded_artists': Artist.objects.filter(exclude=True).count(),
        'num_included_artists': Artist.objects.filter(include=True).count(),
        'concerts_abroad_today': Concert.objects.filter(date=datetime.now().date()).exclude(relationconcertorganisation__organisation__location__country__name='Belgium')
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class ConcertsMergeForm(forms.ModelForm):
    artist = autocomplete.Select2ListChoiceField(
        choice_list=Artist.objects.all().values_list('mbid', flat=True),
        required=False,
        widget=autocomplete.ListSelect2(
                url='artist_autocomplete'
            )
    )

    class Meta:
        model = ConcertsMerge
        fields = ['primary_object', 'alias_objects']
        widgets = {
            'artist': autocomplete.ModelSelect2(
                url='artist_autocomplete',
                attrs={'data-html': True},
            ),
            'primary_object': autocomplete.ModelSelect2(
                url='concert_autocomplete_no_create',
                attrs={'data-html': True},
                forward=['artist']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='concert_autocomplete_no_create',
                attrs={'data-html': True},
                forward=['primary_object', 'artist']
            ),
        }


class ConcertsMergeCreate(CreateView):
    model = ConcertsMerge
    form_class = ConcertsMergeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertsMergeDelete(DeleteView):
    model = ConcertsMerge

    def get_success_url(self):
        target = self.object.primary_object
        return reverse_lazy('concert_detail', kwargs={'pk': target.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationsMergeForm(forms.ModelForm):
    location = autocomplete.Select2ListChoiceField(
        choice_list=Location.objects.all().values_list('id', flat=True),
        required=False,
        widget=autocomplete.ListSelect2(
            url='location_autocomplete_no_create'
        )
    )

    class Meta:
        model = OrganisationsMerge
        fields = ['primary_object', 'alias_objects']
        widgets = {
            'location': autocomplete.ModelSelect2(
                url='location_autocomplete_no_create'
            ),
            'primary_object': autocomplete.ModelSelect2(
                url='organisation_autocomplete_no_create',
                attrs={'data-html': True},
                forward=['location']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='organisation_autocomplete_no_create',
                attrs={'data-html': True},
                forward=['primary_object', 'location']
            ),
        }


class OrganisationsMergeCreate(CreateView):
    model = OrganisationsMerge
    form_class = OrganisationsMergeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationsMergeDelete(DeleteView):
    model = OrganisationsMerge

    def get_success_url(self):
        target = self.object.primary_object
        return reverse_lazy('organisation_detail', kwargs={'pk': target.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationsMergeForm(forms.ModelForm):
    country = autocomplete.Select2ListChoiceField(
        choice_list=Country.objects.all().values_list('id', flat=True),
        required=False,
        validators=[],
        widget=autocomplete.ListSelect2(
            url='country_autocomplete'
        )
    )

    class Meta:
        model = LocationsMerge
        fields = ['primary_object', 'alias_objects']
        exclude = ('country',)
        widgets = {
            'country': autocomplete.ModelSelect2(
                url='country_autocomplete'
            ),
            'primary_object': autocomplete.ModelSelect2(
                url='location_autocomplete_no_create',
                forward=['country']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='location_autocomplete_no_create',
                forward=['primary_object', 'country']
            ),
        }


class LocationsMergeCreate(CreateView):
    model = LocationsMerge
    form_class = LocationsMergeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationsMergeDelete(DeleteView):
    model = LocationsMerge

    def get_success_url(self):
        target = self.object.primary_object
        return reverse_lazy('location_detail', kwargs={'pk': target.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertOrganisationsListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return ConcertAnnouncement.objects.exclude(concert__isnull=True).exclude(raw_venue__organisation=F('concert__relationconcertorganisation__organisation')).distinct()


class DefaultConcertListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_start'] = self.request.GET.get('filter_start', '2019-01-01')
        context['filter_end'] = self.request.GET.get('filter_end', '2025-12-31')
        context['filter'] = self.request.GET.get('filter', None)
        context['countries'] = Country.objects.all().distinct()
        return context

    def apply_filters(self):
        filter_start = self.request.GET.get('filter_start', '2020-01-01')
        filter_end = self.request.GET.get('filter_end', '2999-12-31')
        filter_val = self.request.GET.get('filter', None)
        if filter_val:
            new_context = Concert.objects.filter(date__gte=filter_start).filter(date__lte=filter_end).filter(relationconcertorganisation__organisation__location__country__name=filter_val)
        else:
            new_context = Concert.objects.filter(date__gte=filter_start).filter(date__lte=filter_end)
        return new_context


class ConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters()


class IgnoredConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(ignore=True)


class ConcertsWithMultipleOrganisationsInDifferentCountries(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().annotate(num_countries=Count('relationconcertorganisation__organisation__location', distinct=True)).filter(num_countries__gte=2)


class RecentlyAddedConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().exclude(verified=True).exclude(ignore=True).order_by('-created_at')


class UpcomingConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(date__gte=datetime.now().date()).order_by('date', 'relationconcertorganisation__organisation__location__country')


class ConcertsWithoutArtistsListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(relationconcertartist__artist__isnull=True)


class ConcertsWithoutOrganisationsListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(relationconcertorganisation__organisation__isnull=True).exclude(ignore=True).exclude(cancelled=True)


class NoGenreConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(genre__isnull=True).exclude(verified=True)


class NoAnnouncementConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(concertannouncement=None).exclude(verified=True)


class ConcertsWithMoreThanOneArtist(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().annotate(num_artists=Count('relationconcertartist')).filter(num_artists__gt=1)


class ConcertForm(forms.ModelForm):
    class Meta:
        model = Concert
        fields = ['date', 'genre', 'cancelled', 'ignore', 'verified', 'latitude', 'longitude', 'annotation']


class ConcertDetailView(DetailView):
    model = Concert

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertCreate(CreateView):
    model = Concert
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertUpdate(UpdateView):
    model = Concert
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertDelete(DeleteView):
    model = Concert
    success_url = reverse_lazy('concerts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ignore_concertannouncements = self.kwargs["concert_delete_with_ca_on_ignore"]
        if ignore_concertannouncements < 2:
            ConcertAnnouncement.objects.filter(concert=self.object).update(ignore=True, concert=None)
        if ignore_concertannouncements == 2:
            ConcertAnnouncement.objects.filter(concert=self.object).delete()
        return context


class ArtistCreate(CreateView):
    model = Artist
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ArtistUpdate(UpdateView):
    model = Artist
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ArtistListView(ListView):
    model = Artist
    paginate_by = 30

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', '')
        new_context = Artist.objects.filter(
            name__iregex=filter_val
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['num_artists'] = Artist.objects.filter(name__iregex=context['filter']).count()
        return context


class IncludeArtistListView(ListView):
    model = Artist
    paginate_by = 30

    def get_queryset(self):
        new_context = Artist.objects.filter(
            include=True
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ExcludeArtistListView(ListView):
    model = Artist
    paginate_by = 30

    def get_queryset(self):
        new_context = Artist.objects.filter(
            exclude=True
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoGenreArtistListView(ListView):
    model = Artist
    paginate_by = 30

    def get_queryset(self):
        new_context = Artist.objects.filter(genre__isnull=True).exclude(relationconcertartist__isnull=True).annotate(num_concerts=Count('relationconcertartist', distinct=True)).filter(num_concerts__gt=5).order_by('-num_concerts')
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ArtistDetailView(DetailView, MultipleObjectMixin):
    model = Artist
    fields = '__all__'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        object_list = Concert.objects.filter(relationconcertartist__artist=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = ConcertForm()
        return context


class LocationForm(forms.ModelForm):
    subcountry = autocomplete.Select2ListCreateChoiceField(
        choice_list=Location.objects.all().values_list("subcountry", flat=True),
        widget=autocomplete.ListSelect2(
            url='subcountry_autocomplete_list',
            forward=['country'],
        ),
    )

    class Meta:
        model = Location
        fields = ['country', 'subcountry', 'city', 'zipcode', 'latitude', 'longitude', 'verified']
        widgets = {
            'country': autocomplete.ModelSelect2(
                url='country_autocomplete',
            ),
        }


class LocationCreate(CreateView):
    model = Location
    form_class = LocationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationUpdateView(UpdateView):
    model = Location
    form_class = LocationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationDeleteView(DeleteView):
    model = Location
    success_url = reverse_lazy('locations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationListView(ListView):
    model = Location
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['filtersearch'] = self.request.GET.get('filtersearch', '')
        context['countries'] = Country.objects.all()
        return context

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', None)
        filter_search = self.request.GET.get('filtersearch', None)
        order = self.request.GET.get('orderby', 'country')
        if filter_search and filter_val:
            return Location.objects.filter(city__unaccent__iregex=filter_search).filter(country__name=filter_val).annotate(num_organisations=Count('organisation')).order_by(order, 'city')
        if not filter_search and filter_val:
            return Location.objects.filter(country__name=filter_val).annotate(num_organisations=Count('organisation')).order_by(order, 'city')
        if filter_search and not filter_val:
            return Location.objects.filter(city__unaccent__iregex=filter_search).annotate(num_organisations=Count('organisation')).order_by(order, 'city')
        if not filter_search and not filter_val:
            return Location.objects.all().annotate(num_organisations=Count('organisation')).order_by(order, 'city')


class CitiesWithoutCountryListView(ListView):
    model = Location
    paginate_by = 30

    def get_queryset(self):
        return Location.objects.filter(country__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RecentlyAddedLocationsListView(ListView):
    model = Location
    paginate_by = 30

    def get_queryset(self):
        return Location.objects.exclude(verified=True).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationDetailView(DetailView, MultipleObjectMixin):
    model = Location
    fields = '__all__'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        order = self.request.GET.get('orderby', 'name')
        object_list = Organisation.objects.filter(location=self.object).annotate(num_concerts=Count('relationconcertorganisation')).order_by(order)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = OrganisationForm()
        return context


class GigfinderURLListView(ListView):
    model = GigFinderUrl
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'sort_name', 'disambiguation', 'website', 'organisation_type', 'genre', 'address', 'location', 'verified', 'start_date', 'start_date_precision', 'end_date', 'end_date_precision', 'latitude', 'longitude', 'annotation', 'active', 'capacity']
        widgets = {
            'location': autocomplete.ModelSelect2(
                url='location_autocomplete'
            ),
        }


class DefaultOrganisationListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['filter_country'] = self.request.GET.get('filter_country', '')
        context['countries'] = Country.objects.all()
        return context

    def apply_filters(self):
        filter_val = self.request.GET.get('filter', '')
        filter_country = self.request.GET.get('filter_country', None)
        order = self.request.GET.get('orderby', 'name')
        if filter_country:
            new_context = Organisation.objects.select_related('location__country').filter(name__iregex=filter_val).filter(location__country__name=filter_country)
        else:
            new_context = Organisation.objects.filter(name__iregex=filter_val,)
        return new_context.annotate(num_concerts=Count('relationconcertorganisation')).order_by(order)


class OrganisationsWithoutVenuesListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(venue__isnull=True).exclude(verified=True)


class OrganisationsWithoutLocationListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(location__isnull=True).exclude(verified=True)


class OrganisationsWithoutGPSListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(latitude__isnull=True).exclude(verified=True)


class OrganisationsWithoutGenreListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(genre__isnull=True).exclude(verified=True)


class OrganisationsWithoutDisambiguationListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(disambiguation__isnull=True)


class OrganisationsWithoutSortNameListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(sort_name="")


class UnverifiedOrganisationListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().exclude(verified=True)


class FullOrganisationListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters()


class OrganisationsWithoutConcertsListView(DefaultOrganisationListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(relationconcertorganisation__isnull=True)


class OrganisationDetailView(DetailView, MultipleObjectMixin):
    model = Organisation
    fields = '__all__'

    def get_context_data(self, **kwargs):
        concert_page = self.request.GET.get('page', 1)
        venue_page = self.request.GET.get('venue_page', 1)
        object_list = Paginator(Concert.objects.filter(relationconcertorganisation__organisation=self.object), 30).page(concert_page)
        venue_list = Paginator(Venue.objects.filter(organisation=self.object).order_by('raw_venue'), 50).page(venue_page)
        context = super().get_context_data(object_list=object_list, venue_list=venue_list, **kwargs)
        context["form"] = ConcertForm()
        return context


class OrganisationCreate(CreateView):
    model = Organisation
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationUpdate(UpdateView):
    form_class = OrganisationForm
    model = Organisation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationDelete(DeleteView):
    model = Organisation
    success_url = reverse_lazy('organisations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "organisation_delete_with_venue_consequences" in self.kwargs:
            venue_consequences = self.kwargs["organisation_delete_with_venue_consequences"]
            if venue_consequences < 2:
                Venue.objects.filter(organisation=self.object).update(organisation=None)
            if venue_consequences == 2:
                Venue.objects.filter(organisation=self.object).update(organisation=None, non_assignable=True)
        return context


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['organisation', 'non_assignable']
        widgets = {
            'organisation': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True}
            ),
        }


class VenuesWithoutOrganisationListView(ListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return Venue.objects.filter(organisation__isnull=True).filter(non_assignable=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenuesWithoutAnnouncementsListView(ListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return Venue.objects.filter(concertannouncement__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UnassignableVenueListView(ListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return Venue.objects.filter(non_assignable=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenueListView(ListView):
    model = Venue
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenueDetailView(DetailView):
    model = Venue
    paginate_by = 30

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', 1)
        object_list = Paginator(ConcertAnnouncement.objects.filter(raw_venue=self.object), 30).page(page)
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context


class VenueCreate(CreateView):
    form_class = VenueForm
    model = Venue

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenueUpdate(UpdateView):
    form_class = VenueForm
    model = Venue

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenueDelete(DeleteView):
    model = Venue
    success_url = reverse_lazy('venues')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementForm(forms.ModelForm):
    class Meta:
        model = ConcertAnnouncement
        fields = ['concert', 'ignore']
        widgets = {
            'artist': autocomplete.ModelSelect2(
                url='artist_autocomplete'
            ),
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            ),
            'raw_venue': autocomplete.ModelSelect2(
                url='venue_autocomplete'
            )
        }


class ConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementsWithoutconcertListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return ConcertAnnouncement.objects.filter(concert__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class IgnoredConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return ConcertAnnouncement.objects.filter(ignore=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementDetailView(DetailView):
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementCreate(CreateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementUpdate(UpdateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementDelete(DeleteView):
    model = ConcertAnnouncement
    success_url = reverse_lazy('concertannouncements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertOrganisationForm(forms.ModelForm):
    class Meta:
        model = RelationConcertOrganisation
        fields = ['concert', 'organisation', 'verified', 'organisation_credited_as', 'relation_type']
        widgets = {
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            ),
            'organisation': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True}
            )
        }


class RelationConcertOrganisationCreate(CreateView):
    form_class = RelationConcertOrganisationForm
    model = RelationConcertOrganisation

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertOrganisationUpdate(UpdateView):
    form_class = RelationConcertOrganisationForm
    model = RelationConcertOrganisation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationConcertOrganisation, pk=self.kwargs.get("pk"))
        return reverse_lazy('concert_detail', kwargs={"pk": relation.concert.id})


class RelationConcertOrganisationDelete(DeleteView):
    model = RelationConcertOrganisation

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("concertid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertArtistForm(forms.ModelForm):
    class Meta:
        model = RelationConcertArtist
        fields = ['artist', 'concert', 'artist_credited_as']
        widgets = {
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            ),
            'artist': autocomplete.ModelSelect2(
                url='artist_autocomplete',
                attrs={'data-html': True},
            )
        }


class RelationConcertArtistCreate(CreateView):
    form_class = RelationConcertArtistForm
    model = RelationConcertArtist

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertArtistUpdate(UpdateView):
    form_class = RelationConcertArtistForm
    model = RelationConcertArtist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationConcertArtist, pk=self.kwargs.get("pk"))
        return reverse_lazy('concert_detail', kwargs={"pk": relation.concert.id})


class RelationConcertArtistDelete(DeleteView):
    model = RelationConcertArtist

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("concertid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationArtistArtistForm(forms.ModelForm):
    class Meta:
        model = RelationArtistArtist
        fields = ['artist_a', 'artist_b', 'start_date', 'start_date_precision', 'end_date', 'end_date_precision', 'relation_type']
        widgets = {
            'artist_a': autocomplete.ModelSelect2(
                url='artist_autocomplete',
                attrs={'data-html': True}
            ),
            'artist_b': autocomplete.ModelSelect2(
                url='artist_autocomplete',
                attrs={'data-html': True}
            )
        }


class RelationArtistArtistCreate(CreateView):
    form_class = RelationArtistArtistForm
    model = RelationArtistArtist

    def get_initial(self):
        artist = get_object_or_404(Artist, pk=self.kwargs.get("pk"))
        return {
            'artist_a': artist,
        }

    def get_success_url(self):
        return reverse_lazy('artist_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationArtistArtistUpdate(UpdateView):
    form_class = RelationArtistArtistForm
    model = RelationArtistArtist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationArtistArtist, pk=self.kwargs.get("pk"))
        return reverse_lazy('artist_detail', kwargs={"pk": relation.artist_a.mbid})


class RelationArtistArtistDelete(DeleteView):
    model = RelationArtistArtist

    def get_success_url(self):
        return reverse_lazy('artist_detail', kwargs={"pk": self.kwargs.get("artistid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationOrganisationOrganisationForm(forms.ModelForm):
    class Meta:
        model = RelationOrganisationOrganisation
        fields = ['organisation_a', 'organisation_b', 'start_date', 'start_date_precision', 'end_date', 'end_date_precision', 'relation_type']
        widgets = {
            'organisation_a': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True}
            ),
            'organisation_b': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True}
            )
        }


class RelationOrganisationOrganisationCreate(CreateView):
    form_class = RelationOrganisationOrganisationForm
    model = RelationOrganisationOrganisation

    def get_initial(self):
        organisation = get_object_or_404(Organisation, pk=self.kwargs.get("pk"))
        return {
            'organisation_a': organisation,
        }

    def get_success_url(self):
        return reverse_lazy('organisation_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationOrganisationOrganisationUpdate(UpdateView):
    form_class = RelationOrganisationOrganisationForm
    model = RelationOrganisationOrganisation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationOrganisationOrganisation, pk=self.kwargs.get("pk"))
        return reverse_lazy('organisation_detail', kwargs={"pk": relation.organisation_a.id})


class RelationOrganisationOrganisationDelete(DeleteView):
    model = RelationOrganisationOrganisation

    def get_success_url(self):
        return reverse_lazy('organisation_detail', kwargs={"pk": self.kwargs.get("organisationid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertConcertForm(forms.ModelForm):
    class Meta:
        model = RelationConcertConcert
        fields = ['concert_a', 'relation_type', 'concert_b']
        widgets = {
            'concert_a': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            ),
            'concert_b': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            )
        }


class RelationConcertConcertCreate(CreateView):
    form_class = RelationConcertConcertForm
    model = RelationConcertConcert

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert_a': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationConcertConcertUpdate(UpdateView):
    form_class = RelationConcertConcertForm
    model = RelationConcertConcert

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationConcertConcert, pk=self.kwargs.get("pk"))
        return reverse_lazy('concert_detail', kwargs={"pk": relation.concert_a.id})


class RelationConcertConcertDelete(DeleteView):
    model = RelationConcertConcert

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("concertid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RecentlyAddedOrganisationListView(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.exclude(verified=True).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationOrganisationIdentifierForm(forms.ModelForm):
    class Meta:
        model = RelationOrganisationIdentifier
        fields = ['organisation', 'identifier', 'start_date', 'start_date_precision', 'end_date', 'end_date_precision']
        widgets = {
            'organisation': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True}
            ),
            'identifier': autocomplete.ModelSelect2(
                url='identifier_autocomplete'
            )
        }


class RelationOrganisationIdentifierCreate(CreateView):
    form_class = RelationOrganisationIdentifierForm
    model = RelationOrganisationIdentifier

    def get_initial(self):
        organisation = get_object_or_404(Organisation, pk=self.kwargs.get("pk"))
        return {
            'organisation': organisation,
        }

    def get_success_url(self):
        return reverse_lazy('organisation_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationOrganisationIdentifierUpdate(UpdateView):
    form_class = RelationOrganisationIdentifierForm
    model = RelationOrganisationIdentifier

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationOrganisationIdentifier, pk=self.kwargs.get("pk"))
        return reverse_lazy('organisation_detail', kwargs={"pk": relation.organisation.id})


class RelationOrganisationIdentifierDelete(DeleteView):
    model = RelationOrganisationIdentifier

    def get_success_url(self):
        return reverse_lazy('organisation_detail', kwargs={"pk": self.kwargs.get("organisationid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class IdentifierCreate(CreateView):
    model = ExternalIdentifier
    fields = fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy('identifier_update', kwargs={"pk": self.kwargs.get("pk")})


class IdentifierUpdateView(UpdateView):
    model = ExternalIdentifier
    fields = fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy('identifier_update', kwargs={"pk": self.kwargs.get("pk")})


class IdentifierDeleteView(DeleteView):
    model = ExternalIdentifier
    fields = fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy('identifier_update', kwargs={"pk": self.kwargs.get("pk")})


class RelationLocationLocationForm(forms.ModelForm):
    class Meta:
        model = RelationLocationLocation
        fields = ['location_a', 'relation_type', 'location_b']
        widgets = {
            'location_a': autocomplete.ModelSelect2(
                url='location_autocomplete'
            ),
            'location_b': autocomplete.ModelSelect2(
                url='location_autocomplete'
            )
        }


class RelationLocationLocationCreate(CreateView):
    form_class = RelationLocationLocationForm
    model = RelationLocationLocation

    def get_initial(self):
        location = get_object_or_404(Location, pk=self.kwargs.get("pk"))
        return {
            'location_a': location,
        }

    def get_success_url(self):
        return reverse_lazy('location_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RelationLocationLocationUpdate(UpdateView):
    form_class = RelationLocationLocationForm
    model = RelationLocationLocation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        relation = get_object_or_404(RelationLocationLocation, pk=self.kwargs.get("pk"))
        return reverse_lazy('location_detail', kwargs={"pk": relation.location_a.id})


class RelationLocationLocationDelete(DeleteView):
    model = RelationLocationLocation

    def get_success_url(self):
        return reverse_lazy('location_detail', kwargs={"pk": self.kwargs.get("locationid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
