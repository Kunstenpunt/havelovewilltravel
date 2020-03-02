from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django import forms
from dal import autocomplete
from django.db.models import Q
from django.db.models.functions import Length

from datetime import datetime

from django.views.generic.list import MultipleObjectMixin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, RelationConcertConcert, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, \
    RelationArtistArtist, OrganisationsMerge, ConcertsMerge


class ConcertAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Concert.objects.all()

        first_selected = self.forwarded.get('primary_object', None)

        if first_selected:
            qs = qs.exclude(id=first_selected)

        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs

    def get_result_label(self, item):
        if item.date:
            return item.title + " (" + item.date.isoformat() + ", " + item.artists() + ", " + item.organisations() + ")"
        else:
            return item.title


class ConcertAnnouncementAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ConcertAnnouncement.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Artist.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class OrganisationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organisation.objects.all()

        first_selected = self.forwarded.get('primary_object', None)

        if first_selected:
            qs = qs.exclude(id=first_selected)

        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def get_result_label(self, item):
        if item.disambiguation or item.location:
            brackets = " (" + (item.disambiguation + ", " if item.disambiguation else "") + (str(item.location) if item.location else "") + ")"
            return item.name + brackets
        else:
            return item.name


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Location.objects.all()
        if self.q:
            qs = qs.filter(Q(city__icontains=self.q) | Q(country__name__icontains=self.q))
        return qs


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Country.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class VenueAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Venue.objects.all()
        if self.q:
            qs = qs.filter(raw_venue__icontains=self.q)
        return qs


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    context = {
        'num_concerts': (Concert.objects.all().count()),
        'num_artists': (Artist.objects.count()),
        'num_organisations': (Organisation.objects.count()),
        'num_venues': Venue.objects.count(),
        'num_announcements': ConcertAnnouncement.objects.count(),
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
        'num_concerts_without_title': Concert.objects.annotate(text_len=Length('title')).filter(text_len__lt=4).count(),
        'num_concerts_without_announcements': Concert.objects.filter(concertannouncement=None).exclude(verified=True).count(),
        'num_organisation_without_concerts': Organisation.objects.filter(relationconcertorganisation__organisation=None).count(),
        'num_artists_without_genre': Artist.objects.filter(genre__isnull=True).count()
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class ConcertsMergeForm(forms.ModelForm):
    class Meta:
        model = ConcertsMerge
        fields = ['primary_object', 'alias_objects']
        widgets = {
            'primary_object': autocomplete.ModelSelect2(
                url='concert_autocomplete'
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='concert_autocomplete',
                forward=['primary_object']
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
    success_url = reverse_lazy('concerts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationsMergeForm(forms.ModelForm):
    class Meta:
        model = OrganisationsMerge
        fields = ['primary_object', 'alias_objects']
        widgets = {
            'primary_object': autocomplete.ModelSelect2(
                url='organisation_autocomplete'
            ),
            'alias_objects': autocomplete.ModelSelect2Multiple(
                url='organisation_autocomplete',
                forward=['primary_object']
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
    success_url = reverse_lazy('organisations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RecentlyAddedConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.exclude(verified=True).exclude(ignore=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UpcomingConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(date__gte=datetime.now().date()).order_by('date', 'relationconcertorganisation__organisation__location__country')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ArtistlessConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(relationconcertartist__artist__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationlessConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(relationconcertorganisation__organisation__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoGpsConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(latitude__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoGenreConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(genre__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoTitleConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.annotate(text_len=Length('title')).filter(text_len__lt=4)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NoAnnouncementConcertListView(ListView):
    model = Concert
    paginate_by = 15

    def get_queryset(self):
        return Concert.objects.filter(concertannouncement=None).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertForm(forms.ModelForm):
    class Meta:
        model = Concert
        fields = ['date', 'genre', 'cancelled', 'ignore', 'verified', 'latitude', 'longitude']


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
    paginate_by = 15

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', '')
        new_context = Artist.objects.filter(
            name__istartswith=filter_val
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        return context


class IncludeArtistListView(ListView):
    model = Artist
    paginate_by = 15

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
    paginate_by = 15

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
    paginate_by = 15

    def get_queryset(self):
        new_context = Artist.objects.filter(genre__isnull=True)
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ArtistDetailView(DetailView, MultipleObjectMixin):
    model = Artist
    fields = '__all__'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        object_list = Concert.objects.filter(relationconcertartist__artist=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = ConcertForm()
        return context


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['city', 'latitude', 'longitude', 'country', 'verified']
        widgets = {
            'country': autocomplete.ModelSelect2(
                url='country_autocomplete'
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
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return Location.objects.exclude(organisation__isnull=True)


class SparseLocationListView(ListView):
    model = Location
    paginate_by = 15

    def get_queryset(self):
        return Location.objects.filter(country__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LocationDetailView(DetailView, MultipleObjectMixin):
    model = Location
    fields = '__all__'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        object_list = Organisation.objects.filter(location=self.object)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = OrganisationForm()
        return context


class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'disambiguation', 'website', 'organisation_type', 'genre', 'location', 'verified', 'start_date', 'end_date', 'latitude', 'longitude', 'annotation', 'active', 'capacity']
        widgets = {
            'location': autocomplete.ModelSelect2(
                url='location_autocomplete'
            ),
        }


class OrganisationListView(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(venue__isnull=True).filter(verified=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView2(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(location__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView3(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(latitude__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView4(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(genre__isnull=True).exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrganisationListView5(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(disambiguation__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UnverifiedOrganisationListView(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.exclude(verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class FullOrganisationListView(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', '')
        new_context = Organisation.objects.filter(
            name__istartswith=filter_val
        )
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        return context


class OrganisationsWithoutConcertsListView(ListView):
    model = Organisation
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.filter(relationconcertorganisation__organisation=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class OrganisationDetailView(DetailView, MultipleObjectMixin):
    model = Organisation
    fields = '__all__'
    paginate_by = 10

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
                url='organisation_autocomplete'
            ),
        }


class SparseVenueListView(ListView):
    model = Venue
    paginate_by = 15

    def get_queryset(self):
        return Venue.objects.filter(organisation__isnull=True).filter(non_assignable=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UnassignableVenueListView(ListView):
    model = Venue
    paginate_by = 15

    def get_queryset(self):
        return Venue.objects.filter(non_assignable=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VenueListView(ListView):
    model = Venue
    paginate_by = 15

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
                url='concert_autocomplete'
            ),
            'raw_venue': autocomplete.ModelSelect2(
                url='venue_autocomplete'
            )
        }


class AllConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 15

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
                url='concert_autocomplete'
            ),
            'organisation': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': False}
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
                url='concert_autocomplete'
            ),
            'artist': autocomplete.ModelSelect2(
                url='artist_autocomplete'
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
        fields = ['artist_a', 'artist_b', 'start_date', 'end_date', 'relation_type']
        widgets = {
            'artist_a': autocomplete.ModelSelect2(
                url='artist_autocomplete'
            ),
            'artist_b': autocomplete.ModelSelect2(
                url='artist_autocomplete'
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
        return reverse_lazy('artist_detail', kwargs={"pk": relation.artist_a.id})


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
        fields = ['organisation_a', 'organisation_b', 'start_date', 'end_date', 'relation_type']
        widgets = {
            'organisation_a': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': False}
            ),
            'organisation_b': autocomplete.ModelSelect2(
                url='organisation_autocomplete',
                attrs={'data-html': False}
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
                url='concert_autocomplete'
            ),
            'concert_b': autocomplete.ModelSelect2(
                url='concert_autocomplete'
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
    paginate_by = 15

    def get_queryset(self):
        return Organisation.objects.exclude(verified=True).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
