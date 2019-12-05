from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django import forms
from dal import autocomplete

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


class RawvenueAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = RawVenue.objects.all()
        if self.q:
            qs = qs.filter(raw_venue__icontains=self.q)
        return qs


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_concerts = Concert.objects.all().count()
    num_artists = Musicbrainz.objects.count()
    num_venues = Organity.objects.count()

    context = {
        'num_concerts': num_concerts,
        'num_artists': num_artists,
        'num_venues': num_venues,
        'num_concertannouncements_without_concerts': ConcertAnnouncement.objects.filter(concert__isnull=True).count(),
        'num_concerts_without_artists': Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True).count(),
        'num_concerts_without_organities': Concert.objects.filter(relationconcertorganity__organity__isnull=True).count(),
        'num_rawvenues_without_organities': RawVenue.objects.filter(venue__isnull=True).count(),
        'num_organities_without_rawvenues': Organity.objects.filter(rawvenue__isnull=True).count()
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class ConcertListView(generic.ListView):
    model = Concert
    paginate_by = 25


class ArtistlessConcertListView(generic.ListView):
    model = Concert
    paginate_by = 25

    def get_queryset(self):
        return Concert.objects.filter(relationconcertmusicbrainz__musicbrainz__isnull=True)


class VenuelessConcertListView(generic.ListView):
    model = Concert
    paginate_by = 25

    def get_queryset(self):
        return Concert.objects.filter(relationconcertorganity__organity__isnull=True)


class ConcertDetailView(generic.DetailView):
    model = Concert


class ConcertCreate(CreateView):
    model = Concert
    fields = '__all__'


class ConcertUpdate(UpdateView):
    model = Concert
    fields = '__all__'


class ConcertDelete(DeleteView):
    model = Concert
    success_url = reverse_lazy('concerts')


class MusicbrainzListView(generic.ListView):
    model = Musicbrainz
    paginate_by = 25


class MusicbrainzDetailView(generic.DetailView):
    model = Musicbrainz


class OrganityListView(generic.ListView):
    model = Organity
    paginate_by = 25

    def get_queryset(self):
        return Organity.objects.filter(rawvenue__isnull=True)


class FullOrganityListView(generic.ListView):
    model = Organity
    paginate_by = 25


class OrganityDetailView(generic.DetailView):
    model = Organity


class OrganityCreate(CreateView):
    model = Organity
    fields = '__all__'


class OrganityUpdate(UpdateView):
    model = Organity
    fields = '__all__'


class OrganityDelete(DeleteView):
    model = Organity
    success_url = reverse_lazy('organities')


class RawvenueForm(forms.ModelForm):
    class Meta:
        model = RawVenue
        fields = ['raw_venue', 'venue']
        widgets = {
            'venue': autocomplete.ModelSelect2(
                url='organity_autocomplete'
            ),
        }


class RawvenueListView(generic.ListView):
    model = RawVenue
    paginate_by = 25

    def get_queryset(self):
        return RawVenue.objects.filter(venue__isnull=True)


class RawvenueDetailView(generic.DetailView):
    model = RawVenue


class RawvenueCreate(CreateView):
    form_class = RawvenueForm
    model = RawVenue


class RawvenueUpdate(UpdateView):
    form_class = RawvenueForm
    model = RawVenue


class RawvenueDelete(DeleteView):
    model = RawVenue
    success_url = reverse_lazy('rawvenues')


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


class ConcertAnnouncementListView(generic.ListView):
    model = ConcertAnnouncement
    paginate_by = 25

    def get_queryset(self):
        return ConcertAnnouncement.objects.filter(concert__isnull=True)


class ConcertAnnouncementDetailView(generic.DetailView):
    model = ConcertAnnouncement


class ConcertAnnouncementCreate(CreateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement


class ConcertAnnouncementUpdate(UpdateView):
    form_class = ConcertAnnouncementForm
    model = ConcertAnnouncement


class ConcertAnnouncementDelete(DeleteView):
    model = ConcertAnnouncement
    success_url = reverse_lazy('concertannouncements')


class RelationConcertOrganityCreate(CreateView):
    model = RelationConcertOrganity
    fields = '__all__'

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})


class RelationConcertOrganityUpdate(UpdateView):
    model = RelationConcertOrganity
    fields = '__all__'


class RelationConcertOrganityDelete(DeleteView):
    model = RelationConcertOrganity

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})


class RelationConcertMusicbrainzCreate(CreateView):
    model = RelationConcertMusicbrainz
    fields = '__all__'

    def get_initial(self):
        concert = get_object_or_404(Concert, pk=self.kwargs.get("pk"))
        return {
            'concert': concert,
        }

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})


class RelationConcertMusicbrainzUpdate(UpdateView):
    model = RelationConcertMusicbrainz
    fields = '__all__'


class RelationConcertMusicbrainzDelete(DeleteView):
    model = RelationConcertMusicbrainz

    def get_success_url(self):
        return reverse_lazy('concert_detail', kwargs={"pk": self.kwargs.get("pk")})
