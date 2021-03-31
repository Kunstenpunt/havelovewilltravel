from django.shortcuts import render, get_object_or_404, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.forms import modelform_factory
from django.urls import reverse_lazy, reverse
from django import forms
from dal import autocomplete
from django.db.models import Q, Exists, Count, F, Max, DateField
from django.db.models.functions import Length
from django.db.models import Prefetch
from django.utils.html import format_html

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from itertools import chain
from datetime import datetime, timedelta
from simple_history.models import HistoricalChanges
from collections import Counter
from django.views.generic.list import MultipleObjectMixin

from .forms import ConcertForm, GigFinderUrlFormset
from .choices import get_role_choices

from .models import Concert, ConcertAnnouncement, Artist, Organisation, OrganisationType, Location, Genre, RelationConcertConcert, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, \
    RelationArtistArtist, OrganisationsMerge, ConcertsMerge, LocationsMerge, GigFinderUrl, RelationOrganisationIdentifier, \
    ExternalIdentifier, RelationLocationLocation, RelationLocationLocationType

from bootstrap_modal_forms.forms import BSModalForm
from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django_super_deduper.merge import MergedModelInstance

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
        if item:
            return format_html('{} <i>{}</i> -- <a target="_blank" href="{}">ctrl+click to open</a>', item.name, (item.disambiguation if item.disambiguation else "No disambiguation"), item.get_absolute_url())
        else:
            return item.name


class ArtistAutocompleteSelect(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Artist.objects.all()
        if self.q:
            qs = qs.filter(name__unaccent__istartswith=self.q)
        return qs

    def get_result_label(self, item):
        return item.name


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


class OrganisationAutocompleteSelect(autocomplete.Select2QuerySetView):
    template_name='templates/hlwtadmin/organisation_autocomplete.html'

    def get_queryset(self):
        qs = Organisation.objects.all()

        location = self.forwarded.get('location', None)
        if location:
            qs = qs.filter(location__id=location)

        if self.q:
            qs = qs.filter(name__unaccent__iregex=self.q)
        return qs

    def get_result_label(self, item):
        return(
            f'{item.name[0:80]}, '
            f'{item.location if item.location else "No location"}'
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


class LocationAutocompleteSelect(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Location.objects.all()

        country = self.forwarded.get('country', None)

        if country:
            qs = qs.filter(country__id=country)

        if self.q:
            qs = qs.filter(city__unaccent__iregex=self.q)
            if not qs:
                qs = qs.filter(country__unaccent__iregex=self.q)
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
    lookback = 15
    concert_changes = Concert.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
    relationconcertorganisation_changes = RelationConcertOrganisation.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
    relationconcertartist_changes = RelationConcertArtist.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
    location_changes = Location.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
    report = chain(concert_changes, relationconcertorganisation_changes, relationconcertartist_changes, location_changes)
    report = sorted(report, key=lambda x: x.history_date, reverse=True)
    leeches = Counter([item.history_change_reason for item in report])
    leeches = sorted([leech for leech in leeches.most_common() if leech[0].startswith('automatic_')], key=lambda x: x[0], reverse=True)
    
    concerts_abroad_today = Concert.objects.filter(
        date=datetime.now().date()
        ).exclude(organisation__location__country__name='Belgium'
        ).prefetch_related(
            Prefetch('artist',Artist.objects.all(), to_attr='related_artists'),
            Prefetch('organisation',Organisation.objects.all(), to_attr='related_organisations'),
            ).all()

    # Generate counts of some of the main objects
    context = {
        'leeches': leeches,
        'num_concerts': Concert.objects.count(),
        'num_artists': Artist.objects.count(),
        'num_organisations': Organisation.objects.count(),
        'num_venues': Venue.objects.count(),
        'num_announcements': ConcertAnnouncement.objects.count(),
        'num_locations': Location.objects.count(),
        'num_excluded_artists': Artist.objects.filter(exclude=True).count(),
        'num_included_artists': Artist.objects.filter(include=True).count(),
        'concerts_abroad_today': concerts_abroad_today
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


class ConcertsMergeUpdate(UpdateView):
    model = ConcertsMerge
    form_class = ConcertsMergeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertsMergeConfirm(DeleteView):
    model = ConcertsMerge

    def get_success_url(self):
        target = self.object.primary_object
        self.object.merge()
        return reverse_lazy('concert_detail', kwargs={'pk': target.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertsMergeDelete(DeleteView):
    model = ConcertsMerge

    def get_success_url(self):
        return reverse_lazy('concertsmerges')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertsMergeList(ListView):
    model = ConcertsMerge
    paginate_by = 30

    def get_queryset(self):
        new_context = ConcertsMerge.objects.all()
        return new_context

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
        now = datetime.now()
        context['filter_start'] = self.request.GET.get('filter_start', (now - timedelta(days=365)).date().isoformat())
        context['filter_end'] = self.request.GET.get('filter_end', (now + timedelta(days=365)).date().isoformat())
        # checks because if filter start with '' gets through otherwise
        if not context['filter_start']:
            context['filter_start'] = (now - timedelta(days=365)).date().isoformat()
        if not context['filter_end']:
            context['filter_end'] = (now + timedelta(days=365)).date().isoformat()
        context['filter'] = self.request.GET.get('filter', None)
        context['countries'] = Country.objects.all()
        context['genres'] = Genre.objects.all()
        # had to rename variables because otherwise name clash in frontend
        context['start'] = context['filter_start']
        context['end'] = context['filter_end']
        return context

    def apply_filters(self):
        now = datetime.now()
        filter_start = self.request.GET.get('filter_start', (now - timedelta(days=365)).date().isoformat())
        # checks because if filter start with '' gets through otherwise
        if not filter_start:
            filter_start = (now - timedelta(days=365)).date().isoformat()
        filter_end = self.request.GET.get('filter_end', (now + timedelta(days=365)).date().isoformat())
        if not filter_end:
            filter_end = (now + timedelta(days=365)).date().isoformat()
        filter_val = self.request.GET.get('filter', None)
        filter_genre = self.request.GET.get('genrefilter', None)
        filter_loc = self.request.GET.get('location', None)

        basic_query= Q(date__gte=filter_start)
        basic_query.add(Q(date__lte=filter_end),Q.AND)
        if filter_val:
            basic_query.add(Q(organisation__location__country__name=filter_val),Q.AND)
        if filter_genre:
            basic_query.add(Q(genre__name=filter_genre),Q.AND)
        if filter_loc:
            basic_query.add(Q(organisation__location__pk=filter_loc),Q.AND)

        organisations = Organisation.objects.select_related('location','location__country')
        concertannouncements = ConcertAnnouncement.objects.select_related('gigfinder','artist')

        # why the duplication?
        new_context = Concert.objects.filter(
            basic_query
            ).prefetch_related(
                Prefetch('artist',Artist.objects.all().annotate(credited_as=F('relationconcertartist__artist_credited_as')).distinct(), to_attr='related_artists'),
                Prefetch('organisation', queryset=organisations, to_attr='related_organisations'),
                Prefetch('genre',Genre.objects.all(), to_attr='related_genres'),
                Prefetch('concertannouncement_set', queryset=concertannouncements, to_attr='related_concertannouncements'),
                ).distinct()
        
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


class VagueConcertsAbroadListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(ignore=False).filter(until_date__isnull=False).exclude(organisation__location__country__name="Belgium").order_by("-date")


class ConcertsInNonNeighbouringCountries(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().exclude(relationconcertorganisation__organisation__location__country__name__in=["Belgium", "Luxembourg", "Ireland", "France", "Germany", "United Kingdom", "Netherlands", "Spain", "Portugal", "Italy", "Denmark"]).exclude(verified=True)


class ConcertsWithMultipleOrganisationsInDifferentLocations(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().annotate(num_countries=Count('relationconcertorganisation__organisation__location', distinct=True)).filter(num_countries__gte=2).exclude(verified=True)


class RecentlyAddedConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().exclude(verified=True).exclude(ignore=True).order_by('-created_at')


class UpcomingConcertListView(DefaultConcertListView):
    model = Concert
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(date__gte=datetime.now().date()).order_by('date', 'organisation__location__country')


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


class ConcertDetailView(DetailView):
    model = Concert

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ConcertCreate(CreateView):
    model = Concert
    form_class = ConcertForm

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            example_concert = get_object_or_404(Concert, pk=self.kwargs.get('pk'))
            form = ConcertForm(instance=example_concert, initial={'manual':True, 'longitude': None,'latitude': None })
            context = {'form': form}
            return render(request, 'hlwtadmin/concert_form.html', context)
        
        context = {'form': ConcertForm(initial={'manual':True})}
        return render(request, 'hlwtadmin/concert_form.html', context)


class ConcertUpdate(UpdateView):
    model = Concert
    form_class = ConcertForm


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


def concertcheckduplicate(request):
    if request.method == "POST":
        existing_concerts = Concert.objects.filter(artist=request.POST['artist']).filter(date=request.POST['date'])
        info = [({'title': ec.title, 'date': ec.date, 'link': ec.get_absolute_url()}) for ec in existing_concerts]
        # expand to include range of concerts
        #.filter(created_at__range=(start_date, end_date)))
        return JsonResponse({'data':info})


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
        queryset=GigFinderUrl.objects.filter(artist=self.object)
        if self.request.POST:
            context["gigfinders"] = GigFinderUrlFormset(self.request.POST, queryset=queryset, instance=self.object)
        else:
            context["gigfinders"] = GigFinderUrlFormset(queryset=queryset,instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        gigfinders = context["gigfinders"]
        self.object = form.save()
        if gigfinders.is_valid():
            gigfinders.instance = self.object
            gigfinders.save()
        return super().form_valid(form)


class ArtistListView(ListView):
    model = Artist
    paginate_by = 30

    def get_queryset(self):
        filter_val = self.request.GET.get('filter', '')
        filter_genre = self.request.GET.get('genrefilter', None)
        order = self.request.GET.get('orderby', 'name')
        basic_query= Q(name__unaccent__iregex=filter_val) 

        if filter_genre:
            basic_query.add(Q(genre__name=filter_genre),basic_query.connector)

        gigfinderurl = GigFinderUrl.objects.all()

        new_context = Artist.objects.filter(
            basic_query
            ).prefetch_related(
                Prefetch('genre', Genre.objects.all(), to_attr='related_genres'),
                Prefetch('gigfinderurl_set', queryset=gigfinderurl, to_attr='related_gigfinderurls'),
            ).all()

        return new_context.annotate(num_concerts=Count('relationconcertartist__concert', distinct=True))


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        context['num_artists'] = Artist.objects.filter(name__unaccent__iregex=context['filter']).count()
        context['genres'] = Genre.objects.all()
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
        filter_val = self.request.GET.get('filter', '')

        basic_query= Q(artist=self.object) 

        if filter_val == 'abroad':
            basic_query.add(~Q(organisation__location__country__name="Belgium"), basic_query.connector)
        elif filter_val in ['belgium','Belgium']:
            basic_query.add(Q(organisation__location__country__name="Belgium"), basic_query.connector)
        elif filter_val == 'cancelignore':
            basic_query.add((Q(ignore=True) | Q(cancelled=True)), basic_query.connector)
        elif len(filter_val) > 0:
            basic_query.add(Q(organisation__location__country__name=filter_val), basic_query.connector)

        organisations = Organisation.objects.select_related('location','location__country').distinct()
        concertannouncements = ConcertAnnouncement.objects.select_related('gigfinder','artist').distinct()

        object_list = Concert.objects.filter(
            basic_query
            ).prefetch_related(
                Prefetch('organisation', queryset=organisations, to_attr='related_organisations'),
                Prefetch('concertannouncement_set', queryset=concertannouncements, to_attr='related_concertannouncements'),
            ).annotate(credited_as=F('relationconcertartist__artist_credited_as')).distinct()
        
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["gigfinder"] = GigFinderUrl.objects.filter(artist=self.object).select_related('gigfinder')
        context["similar_artists"] = self.object.find_similar_artists()
        context["roles"] = [d for (d,b) in get_role_choices()]
        context["paginate_by_selection"] = self.get_paginate_by(object_list)
        context["filter"] = filter_val

        return context 

    def get_paginate_by(self, queryset):
        """
        Paginate by specified value in querystring, or use default class property value.
        """
        try:
            int(self.request.GET.get('paginate_by'))
            self.request.session['paginate_by'] = self.request.GET.get('paginate_by')
            return self.request.GET.get('paginate_by', self.paginate_by)
        except:
            if 'paginate_by' in self.request.session:
                if self.request.session['paginate_by']:
                    return self.request.session['paginate_by']
            return self.paginate_by


# solves losing parameters
def refresh_paginate_by(request, pk, page=1, filter=""):
    if request.method == "POST":
        if 'paginate_by' in request.POST:
            request.session['paginate_by'] = request.POST.get('paginate_by')
        # always redirect after each action
        url = reverse('artist_detail', kwargs={"pk": pk})
        if filter:
            return HttpResponseRedirect(f'{url}?filter={filter}&page={page}')
        else:
            return HttpResponseRedirect(f'{url}?page={page}')


def process_detail_artist_bulk_actions(request, pk, page=1, filter=""):
    if request.method == "POST":
        action = request.POST.get('action')
        concert_ids = request.POST.getlist('_selected_action')
        artist = pk

        # things have been selected
        if concert_ids:
            if action == 'merge':
                # check if a target has been selected
                if request.POST.get('merged_with'):
                    concert_target = request.POST.get('merged_with')
                    concert_ids.remove(concert_target)
                    concert_target = Concert.objects.get(pk=concert_target)
                    # retrieve value before it's changed
                    date = concert_target.date
                    until_date = concert_target.until_date
                    concert_sources = Concert.objects.filter(pk__in=concert_ids)
                    mm = MergedModelInstance.create(concert_target, concert_sources)
                    # set date manually to target date
                    mm.date = date
                    mm.until_date = until_date
                    mm.save()

            if action == 'role':
                # check if a role has to be added
                if request.POST.get('add_role') :
                    role = request.POST.get('add_role')
                    RelationConcertArtist.objects.filter(artist=pk,concert_id__in=concert_ids).update(roles=role)

            if action == 'delete':
                # protected foreign keys
                RelationConcertArtist.objects.filter(concert_id__in=concert_ids,artist=pk).delete()
                RelationConcertOrganisation.objects.filter(concert_id__in=concert_ids).delete()
                # related ConcertAnnouncements
                ConcertAnnouncement.objects.filter(concert_id__in=concert_ids).update(ignore=True, concert=None)
                Concert.objects.filter(pk__in=concert_ids).delete()

            if action == 'credited_as':
                if request.POST.get('add_credited'):
                    RelationConcertArtist.objects.filter(concert_id__in=concert_ids,artist=pk).update(artist_credited_as=request.POST.get('add_credited'))
                else:
                    RelationConcertArtist.objects.filter(concert_id__in=concert_ids,artist=pk).update(artist_credited_as=None)

            if action == 'cancelled_status':
                concerts = Concert.objects.filter(id__in=concert_ids)
                for c in concerts:
                    if c.cancelled == None:
                        c.cancelled = True
                    else:
                        c.cancelled = not c.cancelled
                Concert.objects.bulk_update(concerts, ['cancelled'])

            if action == 'ignore_status':
                concerts = Concert.objects.filter(id__in=concert_ids)
                for c in concerts:
                    if c.ignore == None:
                        c.ignore = True
                    else:
                        c.ignore = not c.ignore
                Concert.objects.bulk_update(concerts, ['ignore'])

            if action == 'verified_status':
                concerts = Concert.objects.filter(id__in=concert_ids)
                for c in concerts:
                    if c.verified == None:
                        c.verified = True
                    else:
                        c.verified = not c.verified
                Concert.objects.bulk_update(concerts, ['verified'])


    # always redirect after each action
    url = reverse('artist_detail', kwargs={"pk": pk})
    if filter:
        return HttpResponseRedirect(f'{url}?filter={filter}&page={page}')
    else:
        return HttpResponseRedirect(f'{url}?page={page}')


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
        fields = ['country', 'subcountry', 'city', 'zipcode', 'latitude', 'longitude', 'verified', 'disambiguation']
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
        # order by is functional? 
        order = self.request.GET.get('orderby', 'country')

        basic_query= Q() 

        if filter_val:
            basic_query.add(Q(country__name=filter_val),basic_query.connector)
        if filter_search:
            basic_query.add(Q(city__unaccent__iregex=filter_search),basic_query.connector)

        new_context = Location.objects.filter(
            basic_query
            ).select_related('country'
            ).all()

        return new_context.annotate(num_organisations=Count('organisation')).order_by(order, 'city')


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
        locations = [subloc[0] for subloc in RelationLocationLocation.objects.filter(location_b=self.object).filter(relation_type__pk=1).values_list('location_a')] # id=1 > is part of
        locations.append(self.object.pk)
        object_list = Organisation.objects.filter(location__pk__in=locations).annotate(num_concerts=Count('relationconcertorganisation')).order_by(order)
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
        
        basic_query= Q(name__unaccent__iregex=filter_val) 

        if filter_country:
            basic_query.add(Q(location__country__name=filter_country),basic_query.connector)

        organisation_type = OrganisationType.objects.all()

        new_context = Organisation.objects.filter(
            basic_query
            ).select_related('location','location__country'
            ).prefetch_related(
                Prefetch('genre', Genre.objects.all(), to_attr='related_genres'),
                Prefetch('organisation_type', queryset=organisation_type, to_attr='related_organisation_types'),
            ).all()

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
        organisations = [suborg[0] for suborg in RelationOrganisationOrganisation.objects.filter(organisation_b=self.object).values_list('organisation_a')]
        organisations.append(self.object.pk)
        
        #organisations = Organisation.objects.select_related('location','location__country')
        concertannouncements = ConcertAnnouncement.objects.select_related('gigfinder','artist')

        concerts = Concert.objects.filter(organisation__pk__in=organisations
                    ).prefetch_related(
                        Prefetch('organisation', Organisation.objects.all(), to_attr='related_organisations'),
                        Prefetch('artist', Artist.objects.all(), to_attr='related_artists'),
                        Prefetch('concertannouncement_set', queryset=concertannouncements, to_attr='related_concertannouncements'),
                    )#.distinct() ?
        object_list = Paginator(concerts, 30).page(concert_page)
        venue_list = Paginator(Venue.objects.filter(organisation=self.object).order_by('raw_venue'), 50).page(venue_page)
        context = super().get_context_data(object_list=object_list, venue_list=venue_list, **kwargs)
        context["count"] = concerts.count()
        context["genre"] = self.object.genre.all()
        context["organisation_type"] = self.object.organisation_type.all()
        context["similar_organisations"] = self.object.find_similar_organisations()
        context["identifiers"] = self.object.identifiersqs()
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


class DefaultVenueListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', '')
        return context

    def apply_filters(self):
        filter_val = self.request.GET.get('filter', '')
        new_context = Venue.objects.filter(raw_venue__unaccent__iregex=filter_val)
        return new_context


class VenuesWithoutOrganisationListView(DefaultVenueListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(organisation__isnull=True).filter(non_assignable=False)


class VenuesWithoutAnnouncementsListView(DefaultVenueListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(concertannouncement__isnull=True)


class UnassignableVenueListView(DefaultVenueListView):
    model = Venue
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(non_assignable=True)


class VenueListView(DefaultVenueListView):
    model = Venue
    paginate_by = 50

    def get_queryset(self):
        return self.apply_filters()


class VenueDetailView(DetailView, MultipleObjectMixin):
    model = Venue
    fields = '__all__'

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', 1)
        object_list = Paginator(ConcertAnnouncement.objects.filter(raw_venue=self.object), 50).page(page)
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = ConcertAnnouncementForm()
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
                url='artist_autocomplete',
                attrs={'data-html': True}
            ),
            'concert': autocomplete.ModelSelect2(
                url='concert_autocomplete',
                attrs={'data-html': True}
            ),
            'raw_venue': autocomplete.ModelSelect2(
                url='venue_autocomplete'
            )
        }


class ArtistAutocompleteForm(forms.ModelForm):
    class Meta:
        model = ConcertAnnouncement
        fields = ['artist']
        widgets = {
            'artist': autocomplete.ModelSelect2(
                url='artist_autocomplete',
                attrs={'data-html': True}
            ),
        }


class ConcertAnnouncementLeechListView(ListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_context_date(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        new_context = ConcertAnnouncement.history.exclude(history_change_reason=None)
        return new_context


class DefaultConcertAnnouncementListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ArtistAutocompleteForm
        return context

    def apply_filters(self):
        filter_val = self.request.GET.get('artist', None)
        if filter_val:
            new_context = ConcertAnnouncement.objects.filter(artist__mbid=filter_val)
        else:
            new_context = ConcertAnnouncement.objects.all()
        return new_context


class ConcertAnnouncementListView(DefaultConcertAnnouncementListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters()


class ConcertAnnouncementsWithoutconcertListView(DefaultConcertAnnouncementListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(concert__isnull=True)


class IgnoredConcertAnnouncementListView(DefaultConcertAnnouncementListView):
    model = ConcertAnnouncement
    paginate_by = 30

    def get_queryset(self):
        return self.apply_filters().filter(ignore=True)


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


class UserList(ListView, MultipleObjectMixin):
    model = User
    paginate_by = 30

    def get_context_data(self, **kwargs):
        page_report = self.request.GET.get('page_report', 1)
        lookback = 15
        concert_changes = Concert.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
        relationconcertorganisation_changes = RelationConcertOrganisation.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
        relationconcertartist_changes = RelationConcertArtist.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
        location_changes = Location.history.filter(history_user__isnull=True).filter(history_date__gt=datetime.now() - timedelta(days=lookback)).exclude(history_change_reason__isnull=True)
        report = chain(concert_changes, relationconcertorganisation_changes, relationconcertartist_changes, location_changes)
        report = sorted(report, key=lambda x: x.history_date, reverse=True)
        leeches = set([item.history_change_reason for item in report])
        leeches = [item for item in leeches if str(item).startswith("automatic_")]
        report_changes = Paginator(list(report), 10).page(page_report)
        context = super().get_context_data(report_changes=report_changes, leeches=leeches, **kwargs)
        return context


class UserDetail(DetailView, MultipleObjectMixin):
    model = User
    fields = '__all__'

    def get_context_data(self, **kwargs):
        page_report = self.request.GET.get('page_report', 1)
        lookback = 100
        concert_changes = Concert.history.filter(history_user=self.object.pk).filter(history_date__gt=datetime.now() - timedelta(days=lookback))
        relationconcertorganisation_changes = RelationConcertOrganisation.history.filter(history_user=self.object.pk).filter(history_date__gt=datetime.now() - timedelta(days=lookback))
        relationconcertartist_changes = RelationConcertArtist.history.filter(history_user=self.object.pk).filter(history_date__gt=datetime.now() - timedelta(days=lookback))
        location_changes = Location.history.filter(history_user=self.object.pk).filter(history_date__gt=datetime.now() - timedelta(days=lookback))
        report = chain(concert_changes, relationconcertorganisation_changes, relationconcertartist_changes, location_changes)
        report = sorted(report, key=lambda x: x.history_date, reverse=True)
        report_changes = Paginator(report, 10).page(page_report)
        context = super().get_context_data(object_list=[], report_changes=report_changes, **kwargs)
        return context


def get_change(self):
    old_record = self.prev_record
    if old_record:
        delta = self.diff_against(old_record)
        return delta


def get_model(self):
    return self._meta.model_name

setattr(HistoricalChanges, 'get_change', get_change)
setattr(HistoricalChanges, 'get_model', get_model)
