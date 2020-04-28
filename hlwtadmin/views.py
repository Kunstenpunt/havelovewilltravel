from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django import forms
from dal import autocomplete
from django.db.models import Q, Exists, Count
from django.db.models.functions import Length
from django.utils.html import format_html

from datetime import datetime

from django.views.generic.list import MultipleObjectMixin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, RelationConcertConcert, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, \
    RelationArtistArtist, OrganisationsMerge, ConcertsMerge, LocationsMerge, GigFinderUrl


class SubcountryAutocompleteFromList(autocomplete.Select2ListView):
    def get_list(self):
        qs = Location.objects.all()

        country = self.forwarded.get('country', None)

        if country:
            qs = qs.filter(country=country)

        if self.q:
            qs = qs.filter(subcountry__unaccent__icontains=self.q)
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
            qs = qs.filter(title__unaccent__icontains=self.q)
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
            qs = qs.filter(title__unaccent__icontains=self.q)
        return qs


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Artist.objects.all()
        if self.q:
            qs = qs.filter(name__unaccent__icontains=self.q)
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
            qs = qs.filter(name__unaccent__icontains=self.q)
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
            qs = qs.filter(Q(city__unaccent__icontains=self.q) | Q(country__name__unaccent__icontains=self.q))
        return qs


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Country.objects.all()
        if self.q:
            qs = qs.filter(name__unaccent__icontains=self.q)
        return qs


class VenueAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Venue.objects.all()
        if self.q:
            qs = qs.filter(raw_venue__unaccent__icontains=self.q)
        return qs


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    context = {
        'num_concerts': Concert.objects.all().count(),
        'num_artists': Artist.objects.count(),
        'num_organisations': Organisation.objects.count(),
        'num_venues': Venue.objects.count(),
        'num_announcements': ConcertAnnouncement.objects.count(),
        'num_locations': Location.objects.count(),
        'num_concertannouncements_without_concerts': ConcertAnnouncement.objects.filter(concert__isnull=True).count(),
        'num_concerts_without_artists': Concert.objects.filter(relationconcertartist__artist__isnull=True).count(),
        'num_concerts_without_organities': Concert.objects.filter(relationconcertorganisation__organisation__isnull=True).count(),
        'num_rawvenues_without_organities': Venue.objects.filter(organisation__isnull=True).filter(non_assignable=False).count(),
        'num_organities_without_rawvenues': Organisation.objects.filter(venue__isnull=True).filter(verified=False).count(),
        'num_organities_without_locations': Organisation.objects.filter(location__isnull=True).exclude(verified=True).count(),
        'num_cities_without_countries': Location.objects.filter(country__isnull=True).count(),
        'num_unverified_organisations': Organisation.objects.exclude(verified=True).count(),
        'num_excluded_artists': Artist.objects.filter(exclude=True).count(),
        'num_included_artists': Artist.objects.filter(include=True).count(),
        'num_orgs_without_gps': Organisation.objects.filter(latitude__isnull=True).exclude(verified=True).count(),
        'num_orgs_without_genre': Organisation.objects.filter(genre__isnull=True).exclude(verified=True).count(),
        'num_orgs_without_disambiguation': Organisation.objects.filter(disambiguation__isnull=True).count(),
        'num_unassignable_venues': Venue.objects.filter(non_assignable=True).count(),
        'num_concerts_without_gps': Concert.objects.filter(latitude__isnull=True).exclude(verified=True).count(),
        'num_concerts_without_genre': Concert.objects.filter(genre__isnull=True).exclude(verified=True).count(),
        'num_concerts_without_title': Concert.objects.annotate(text_len=Length('title')).filter(text_len__lt=5).count(),
        'num_concerts_without_announcements': Concert.objects.filter(concertannouncement=None).exclude(verified=True).count(),
        'num_organisation_without_concerts': Organisation.objects.filter(relationconcertorganisation__organisation=None).count(),
        'num_artists_without_genre': Artist.objects.filter(genre__isnull=True).exclude(relationconcertartist__isnull=True).count()
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
                url='artist_autocomplete'
            ),
            'primary_object': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True},
                forward=['artist']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='concert_autocomplete',
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
            url='location_autocomplete'
        )
    )

    class Meta:
        model = OrganisationsMerge
        fields = ['primary_object', 'alias_objects']
        widgets = {
            'location': autocomplete.ModelSelect2(
                url='location_autocomplete'
            ),
            'primary_object': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': True},
                forward=['location']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='organisation_autocomplete',
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
                url='location_autocomplete',
                forward=['country']
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='location_autocomplete',
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


class ConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_start'] = self.request.GET.get('filter_start', '1900-01-01')
        context['filter_end'] = self.request.GET.get('filter_end', '2999-12-31')
        context['num_concerts'] = Concert.objects.filter(date__gte=context['filter_start']).filter(date__lte=context['filter_end']).count()
        return context

    def get_queryset(self):
        filter_start = self.request.GET.get('filter_start', '1900-01-01')
        filter_end = self.request.GET.get('filter_end', '2999-12-31')
        new_context = Concert.objects.filter(date__gte=filter_start).filter(date__lte=filter_end)
        return new_context


class RecentlyAddedConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.exclude(verified=True).exclude(ignore=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.exclude(verified=True).exclude(ignore=True).order_by('-created_at').count()
        return context


class UpcomingConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(date__gte=datetime.now().date()).order_by('date', 'relationconcertorganisation__organisation__location__country')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.filter(date__gte=datetime.now().date()).order_by('date', 'relationconcertorganisation__organisation__location__country').count()
        return context


class ArtistlessConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(relationconcertartist__artist__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationlessConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(relationconcertorganisation__organisation__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoGpsConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(latitude__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoGenreConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(genre__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoTitleConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.annotate(text_len=Length('title')).filter(text_len__lt=5)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoAnnouncementConcertListView(ListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return Concert.objects.filter(concertannouncement=None).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


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
            name__unaccent__icontains=filter_val
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['num_artists'] = Artist.objects.filter(name__unaccent__icontains=context['filter']).count()
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


class LocationListView(ListView):
    model = Location
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['filtersearch'] = self.request.GET.get('filtersearch', '')
        context['num_locations'] = Location.objects.filter(city__icontains=context['filtersearch']).filter(country__name=context['filter']).exclude(organisation__location=None).count()
        context['countries'] = Country.objects.all()
        return context

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', None)
        filter_search = self.request.GET.get('filtersearch', None)
        order = self.request.GET.get('orderby', 'country')
        if filter_search and filter_val:
            return Location.objects.filter(city__unaccent__icontains=filter_search).filter(country__name=filter_val).exclude(organisation__location=None).order_by(order)
        if not filter_search and filter_val:
            return Location.objects.filter(country__name=filter_val).exclude(organisation__location=None).order_by(order)
        if filter_search and not filter_val:
            return Location.objects.filter(city__unaccent__icontains=filter_search).exclude(organisation__location=None).order_by(order)
        if not filter_search and not filter_val:
            return Location.objects.exclude(organisation__location=None).order_by(order)


class SparseLocationListView(ListView):
    model = Location
    paginate_by = 30

    def get_queryset(self):
        return Location.objects.filter(country__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationDetailView(DetailView, MultipleObjectMixin):
    model = Location
    fields = '__all__'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        object_list = Organisation.objects.filter(location=self.object)
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
        fields = ['name', 'disambiguation', 'website', 'organisation_type', 'genre', 'address', 'location', 'verified', 'start_date', 'start_date_precision', 'end_date', 'end_date_precision', 'latitude', 'longitude', 'annotation', 'active', 'capacity']
        widgets = {
            'location': autocomplete.ModelSelect2(
                url='location_autocomplete'
            ),
        }


class OrganisationListView(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(venue__isnull=True).filter(verified=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView2(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(location__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView3(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(latitude__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView4(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(genre__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView5(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(disambiguation__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UnverifiedOrganisationListView(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class FullOrganisationListView(ListView):
    model = Organisation
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['num_organisations'] = Organisation.objects.filter(name__unaccent__icontains=context['filter']).exclude(relationconcertorganisation__organisation=None).count()
        return context

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', '')
        new_context = Organisation.objects.filter(name__unaccent__icontains=filter_val,).exclude(relationconcertorganisation__organisation=None)
        return new_context


class OrganisationsWithoutConcertsListView(ListView):
    model = Organisation
    paginate_by = 30

    def get_queryset(self):
        return Organisation.objects.filter(relationconcertorganisation__organisation=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationDetailView(DetailView, MultipleObjectMixin):
    model = Organisation
    fields = '__all__'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        object_list = Concert.objects.filter(relationconcertorganisation__organisation=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
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


class SparseVenueListView(ListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return Venue.objects.filter(organisation__isnull=True).filter(non_assignable=False)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class AllConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return ConcertAnnouncement.objects.filter(concert__isnull=True)

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
