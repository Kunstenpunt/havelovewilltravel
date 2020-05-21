from django.urls import path
from . import views, models


urlpatterns = [
    path('', views.index, name='index'),
    # concerts
    path('concerts/', views.ConcertListView.as_view(), name='concerts'),
    path('organisationless_concerts/', views.OrganisationlessConcertListView.as_view(), name='organisationless_concerts'),
    path('artistless_concerts/', views.ArtistlessConcertListView.as_view(), name='artistless_concerts'),
    path('recently_added_concerts/', views.RecentlyAddedConcertListView.as_view(), name='recently_added_concerts'),
    path('upcoming_concerts/', views.UpcomingConcertListView.as_view(), name='upcoming_concerts'),
    path('concerts_without_gps/', views.NoGpsConcertListView.as_view(), name='concerts_without_gps'),
    path('concerts_without_genre/', views.NoGenreConcertListView.as_view(), name='concerts_without_genre'),
    path('concerts_without_title/', views.NoTitleConcertListView.as_view(), name='concerts_without_title'),
    path('concerts_without_announcements/', views.NoAnnouncementConcertListView.as_view(), name='concerts_without_announcements'),
    path('concerts_with_multiple_organisations_in_different_countries/', views.ConcertsWithMultipleOrganisationsInDifferentCountries.as_view(), name='concerts_with_multiple_organisations_in_different_countries'),
    path('concerts_with_only_deleted_setlist_announcements/', views.OnlyDeletedSetlistAnnouncementConcertListView.as_view(), name='concerts_with_only_deleted_setlist_announcements'),
    path('concert/<int:pk>', views.ConcertDetailView.as_view(), name='concert_detail'),
    path('concert/create/', views.ConcertCreate.as_view(), name='concert_create'),
    path('concert/<int:pk>/update/', views.ConcertUpdate.as_view(), name='concert_update'),
    path('concert/<int:pk>/delete/', views.ConcertDelete.as_view(), name='concert_delete'),
    path('concert/<int:pk>/delete/<int:concert_delete_with_ca_on_ignore>', views.ConcertDelete.as_view(), name='concert_delete_with_ca_on_ignore'),
    # artists
    path('artists/', views.ArtistListView.as_view(), name='artists'),
    path('includeartists/', views.IncludeArtistListView.as_view(), name='includeartists'),
    path('excludeartists/', views.ExcludeArtistListView.as_view(), name='excludeartists'),
    path('artists_without_genre/', views.NoGenreArtistListView.as_view(), name='artists_without_genre'),
    path('artist/<str:pk>', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('artist/create/', views.ArtistCreate.as_view(), name='artist_create'),
    path('artist/<str:pk>/update', views.ArtistUpdate.as_view(), name='artist_update'),
    # locations
    path('locations/', views.LocationListView.as_view(), name='locations'),
    path('sparselocations/', views.SparseLocationListView.as_view(), name='sparse_locations'),
    path('location/<int:pk>', views.LocationDetailView.as_view(), name='location_detail'),
    path('location/<int:pk>/update', views.LocationUpdateView.as_view(), name='location_update'),
    path('location/<int:pk>/delete', views.LocationDeleteView.as_view(), name='location_delete'),
    path('location/create', views.LocationCreate.as_view(), name='location_create'),
    # organisations
    path('sparseorganisation/', views.OrganisationListView.as_view(), name='sparse_organisations'),
    path('sparseorganisation2/', views.OrganisationListView2.as_view(), name='sparse_organisations2'),
    path('organisations_without_gps/', views.OrganisationListView3.as_view(), name='organisations_without_gps'),
    path('organisations_without_genre/', views.OrganisationListView4.as_view(), name='organisations_without_genre'),
    path('organisations_without_disambiguation/', views.OrganisationListView5.as_view(), name='organisations_without_disambiguation'),
    path('organisations_without_concerts/', views.OrganisationsWithoutConcertsListView.as_view(), name='organisations_without_concerts'),
    path('unverified_organisations/', views.UnverifiedOrganisationListView.as_view(), name='unverified_organisations'),
    path('recently_added_organisations/', views.RecentlyAddedOrganisationListView.as_view(), name='recently_added_organisations'),
    path('organisations/', views.FullOrganisationListView.as_view(), name='organisations'),
    path('organisation/<int:pk>', views.OrganisationDetailView.as_view(), name='organisation_detail'),
    path('organisation/create/', views.OrganisationCreate.as_view(), name='organisation_create'),
    path('organisation/<int:pk>/update/', views.OrganisationUpdate.as_view(), name='organisation_update'),
    path('organisation/<int:pk>/delete/', views.OrganisationDelete.as_view(), name='organisation_delete'),
    path('organisation/<int:pk>/delete/<int:organisation_delete_with_venue_consequences>', views.OrganisationDelete.as_view(), name='organisation_delete_with_venue_consequences'),
    # rawvenues
    path('venues/', views.VenueListView.as_view(), name='venues'),
    path('sparsevenues/', views.SparseVenueListView.as_view(), name='sparsevenues'),
    path('unassignable_venues/', views.UnassignableVenueListView.as_view(), name='unassignable_venues'),
    path('venue/<int:pk>', views.VenueDetailView.as_view(), name='venue_detail'),
    path('venue/create/', views.VenueCreate.as_view(), name='venue_create'),
    path('venue/<int:pk>/update/', views.VenueUpdate.as_view(), name='venue_update'),
    path('venue/<int:pk>/delete/', views.VenueDelete.as_view(), name='venue_delete'),
    # gigfinderurls
    path('gigfinderurls/', views.GigfinderURLListView.as_view(), name='gigfinderurls'),
    # concertannouncement
    path('concertannouncements/', views.ConcertAnnouncementListView.as_view(), name='concertannouncements'),
    path('allconcertannouncements/', views.AllConcertAnnouncementListView.as_view(), name='allconcertannouncements'),
    path('concertannouncement/<int:pk>', views.ConcertAnnouncementDetailView.as_view(), name='concertannouncement_detail'),
    path('concertannouncement/create/', views.ConcertAnnouncementCreate.as_view(), name='concertannouncement_create'),
    path('concertannouncement/<int:pk>/update/', views.ConcertAnnouncementUpdate.as_view(), name='concertannouncement_update'),
    path('concertannouncement/<int:pk>/delete/', views.ConcertAnnouncementDelete.as_view(), name='concertannouncement_delete'),
    # relationconcertorganisations
    path('relationconcertorganisations/', views.RelationConcertOrganisationsListView.as_view(), name='relationconcertorganisations'),
    path('relationconcertorganisation/create/<int:pk>', views.RelationConcertOrganisationCreate.as_view(), name='relationconcertorganisation_create'),
    path('relationconcertorganisation/<int:pk>/update/', views.RelationConcertOrganisationUpdate.as_view(), name='relationconcertorganisation_update'),
    path('relationconcertorganisation/<int:pk>/delete/<int:concertid>', views.RelationConcertOrganisationDelete.as_view(), name='relationconcertorganisation_delete'),
    # relationconcertartist
    path('relationconcertartist/create/<int:pk>', views.RelationConcertArtistCreate.as_view(), name='relationconcertartist_create'),
    path('relationconcertartist/<int:pk>/update/', views.RelationConcertArtistUpdate.as_view(), name='relationconcertartist_update'),
    path('relationconcertartist/<int:pk>/delete/<int:concertid>', views.RelationConcertArtistDelete.as_view(), name='relationconcertartist_delete'),
    # relationartistartist
    path('relationartistartist/create/<str:pk>', views.RelationArtistArtistCreate.as_view(), name='relationartistartist_create'),
    path('relationartistartist/<str:pk>/update/', views.RelationArtistArtistUpdate.as_view(), name='relationartistartist_update'),
    path('relationartistartist/<str:pk>/delete/<str:artistid>', views.RelationArtistArtistDelete.as_view(), name='relationartistartist_delete'),

    # relationconcertconcert
    path('relationconcertconcert/create/<str:pk>', views.RelationConcertConcertCreate.as_view(), name='relationconcertconcert_create'),
    path('relationconcertconcert/<str:pk>/update/', views.RelationConcertConcertUpdate.as_view(), name='relationconcertconcert_update'),
    path('relationconcertconcert/<str:pk>/delete/<str:concertid>', views.RelationConcertConcertDelete.as_view(), name='relationconcertconcert_delete'),

    # relationorganisationorganisation
    path('relationorganisationorganisation/create/<int:pk>', views.RelationOrganisationOrganisationCreate.as_view(), name='relationorganisationorganisation_create'),
    path('relationorganisationorganisation/<int:pk>/update/', views.RelationOrganisationOrganisationUpdate.as_view(), name='relationorganisationorganisation_update'),
    path('relationorganisationorganisation/<int:pk>/delete/<int:organisationid>', views.RelationOrganisationOrganisationDelete.as_view(), name='relationorganisationorganisation_delete'),
    # autocompletes
    path('artist-autocomplete/', views.ArtistAutocomplete.as_view(model=models.Artist), name='artist_autocomplete'),
    path('concert-autocomplete/', views.ConcertAutocomplete.as_view(model=models.Concert, create_field='title'), name='concert_autocomplete'),
    path('organisation-autocomplete/', views.OrganisationAutocomplete.as_view(model=models.Organisation, create_field='name'), name='organisation_autocomplete'),
    path('location-autocomplete/', views.LocationAutocomplete.as_view(model=models.Location, create_field='city'), name='location_autocomplete'),
    path('country-autocomplete/', views.CountryAutocomplete.as_view(model=models.Country, create_field='name'), name='country_autocomplete'),
    path('venue-autocomplete/', views.VenueAutocomplete.as_view(model=models.Venue, create_field='raw_venue'), name='venue_autocomplete'),
    path('subcountry-autocomplete-list/', views.SubcountryAutocompleteFromList.as_view(), name='subcountry_autocomplete_list'),
    # merge
    path('organisationsmerge/create/', views.OrganisationsMergeCreate.as_view(model=models.OrganisationsMerge), name='organisationsmerge_create'),
    path('organisationsmerge/<str:pk>/confirm/', views.OrganisationsMergeDelete.as_view(model=models.OrganisationsMerge), name='organisationsmerge_delete'),
    path('concertsmerge/create/', views.ConcertsMergeCreate.as_view(model=models.ConcertsMerge), name='concertsmerge_create'),
    path('concertsmerge/<str:pk>/confirm/', views.ConcertsMergeDelete.as_view(model=models.ConcertsMerge), name='concertsmerge_delete'),
    path('locationsmerge/create/', views.LocationsMergeCreate.as_view(model=models.LocationsMerge), name='locationsmerge_create'),
    path('locationsmerge/<str:pk>/confirm/', views.LocationsMergeDelete.as_view(model=models.LocationsMerge), name='locationsmerge_delete'),
]

from django.conf import settings
from django.urls import include, path  # For django versions from 2.0 and up

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
