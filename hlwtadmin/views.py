from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django import forms
from dal import autocomplete
from django.db.models import Q

from .models import Concert, ConcertAnnouncement, Musicbrainz, Gigfinder, GigfinderUrl, Organity, Address, Location, \
    Country, RelationOrganityOrganity, RelationConcertMusicbrainz, RelationConcertOrganity, RawVenue, OrganityType


class ConcertAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Concert.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs


class ConcertAnnouncementAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ConcertAnnouncement.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs


class MusicbrainzAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Musicbrainz.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class OrganityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organity.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class AddressAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Address.objects.all()
        if self.q:
            qs = qs.filter(Q(location__city__icontains=self.q) | Q(address__icontains=self.q) | Q(location__country__name__icontains=self.q))
        return qs


class RawvenueAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = RawVenue.objects.all()
        if self.q:
            qs = qs.filter(raw_venue__icontains=self.q)
        return qs


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    context = {
        'num_concerts': (Concert.objects.all().count()),
        'num_artists': (Musicbrainz.objects.count()),
        'num_venues': (Organity.objects.count()),
        'num_concertannouncements_without_concerts': ConcertAnnouncement.objects.filter(concert__isnull=True).count(),
        'num_concerts_without_artists': Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count(),
        'num_concerts_without_organities': Concert.objects.filter(relationconcertorganity__organity__isnull=True).count(),
        'num_rawvenues_without_organities': RawVenue.objects.filter(venue__isnull=True).count(),
        'num_organities_without_rawvenues': Organity.objects.filter(rawvenue__isnull=True).count()
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class ConcertListView(ListView):
    model = Concert
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ArtistlessConcertListView(ListView):
    model = Concert
    paginate_by = 25

    def get_queryset(self):
        return Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class VenuelessConcertListView(ListView):
    model = Concert
    paginate_by = 25

    def get_queryset(self):
        return Concert.objects.filter(relationconcertorganity__organity__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertDetailView(DetailView):
    model = Concert

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertCreate(CreateView):
    model = Concert
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertUpdate(UpdateView):
    model = Concert
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertDelete(DeleteView):
    model = Concert
    success_url = reverse_lazy('concerts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class MusicbrainzListView(ListView):
    model = Musicbrainz
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class MusicbrainzDetailView(DetailView):
    model = Musicbrainz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class OrganityForm(forms.ModelForm):
    class Meta:
        model = Organity
        fields = ['name', 'address', 'organity_type']
        widgets = {
            'address': autocomplete.ModelSelect2(
                url='address_autocomplete'
            ),
        }


class OrganityListView(ListView):
    model = Organity
    paginate_by = 25

    def get_queryset(self):
        return Organity.objects.filter(rawvenue__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class FullOrganityListView(ListView):
    model = Organity
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class OrganityDetailView(DetailView):
    model = Organity
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class OrganityCreate(CreateView):
    model = Organity
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class OrganityUpdate(UpdateView):
    form_class = OrganityForm
    model = Organity

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class OrganityDelete(DeleteView):
    model = Organity
    success_url = reverse_lazy('organities')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RawvenueForm(forms.ModelForm):
    class Meta:
        model = RawVenue
        fields = ['raw_venue', 'venue']
        widgets = {
            'venue': autocomplete.ModelSelect2(
                url='organity_autocomplete'
            ),
        }


class RawvenueListView(ListView):
    model = RawVenue
    paginate_by = 25

    def get_queryset(self):
        return RawVenue.objects.filter(venue__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RawvenueDetailView(DetailView):
    model = RawVenue

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RawvenueCreate(CreateView):
    form_class = RawvenueForm
    model = RawVenue

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RawvenueUpdate(UpdateView):
    form_class = RawvenueForm
    model = RawVenue

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RawvenueDelete(DeleteView):
    model = RawVenue
    success_url = reverse_lazy('rawvenues')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertAnnouncementForm(forms.ModelForm):
    class Meta:
        model = ConcertAnnouncement
        fields = ['title', 'musicbrainz', 'date', 'time', 'gigfinder', 'gigfinder_artist_name', 'gigfinder_concert_id', 'concert', 'raw_venue', 'ignore']
        widgets = {
            'musicbrainz': autocomplete.ModelSelect2(
                url='musicbrainz_autocomplete'
            ),
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete'
            )
        }


class ConcertAnnouncementListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 25

    def get_queryset(self):
        return ConcertAnnouncement.objects.filter(concert__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertAnnouncementDetailView(DetailView):
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertAnnouncementCreate(CreateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertAnnouncementUpdate(UpdateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class ConcertAnnouncementDelete(DeleteView):
    model = ConcertAnnouncement
    success_url = reverse_lazy('concertannouncements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertOrganityForm(forms.ModelForm):
    class Meta:
        model = RelationConcertOrganity
        fields = ['concert', 'organity', 'organity_credited_as', 'relation_type']
        widgets = {
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete'
            ),
            'organity': autocomplete.ModelSelect2(
                url='organity_autocomplete'
            )
        }


class RelationConcertOrganityCreate(CreateView):
    form_class = RelationConcertOrganityForm
    model = RelationConcertOrganity

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertOrganityUpdate(UpdateView):
    form_class = RelationConcertOrganityForm
    model = RelationConcertOrganity

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertOrganityDelete(DeleteView):
    model = RelationConcertOrganity

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("concertid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertMusicbrainzForm(forms.ModelForm):
    class Meta:
        model = RelationConcertMusicbrainz
        fields = ['musicbrainz', 'concert']
        widgets = {
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete'
            ),
            'musicbrainz': autocomplete.ModelSelect2(
                url='musicbrainz_autocomplete'
            )
        }


class RelationConcertMusicbrainzCreate(CreateView):
    form_class = RelationConcertMusicbrainzForm
    model = RelationConcertMusicbrainz

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertMusicbrainzUpdate(UpdateView):
    form_class = RelationConcertMusicbrainzForm
    model = RelationConcertMusicbrainz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context


class RelationConcertMusicbrainzDelete(DeleteView):
    model = RelationConcertMusicbrainz

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("concertid")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_concerts'] = Concert.objects.all().count()
        context['num_artists'] = Musicbrainz.objects.count()
        context['num_venues'] = Organity.objects.count()
        context['num_concertannouncements_without_concerts'] = ConcertAnnouncement.objects.filter(concert__isnull=True).count()
        context['num_concerts_without_artists'] = Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count()
        context['num_concerts_without_organities'] = Concert.objects.filter(relationconcertorganity__organity__isnull=True).count()
        context['num_rawvenues_without_organities'] = RawVenue.objects.filter(venue__isnull=True).count()
        context['num_organities_without_rawvenues'] = Organity.objects.filter(rawvenue__isnull=True).count()
        return context
