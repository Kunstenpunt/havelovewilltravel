from django.urls import path
from . import views, models

urlpatterns = [
    path('', views.index, name='index'),
    # concerts
    path('concerts/', views.ConcertListView.as_view(), name='concerts'),
    path('organisationless_concerts/', views.OrganisationlessConcertListView.as_view(), name='organisationless_concerts'),
    path('artistless_concerts/', views.ArtistlessConcertListView.as_view(), name='artistless_concerts'),
    path('concert/<int:pk>', views.ConcertDetailView.as_view(), name='concert_detail'),
    path('concert/create/', views.ConcertCreate.as_view(), name='concert_create'),
    path('concert/<int:pk>/update/', views.ConcertUpdate.as_view(), name='concert_update'),
    path('concert/<int:pk>/delete/', views.ConcertDelete.as_view(), name='concert_delete'),
    # artists
    path('artists/', views.ArtistListView.as_view(), name='artists'),
    path('includeartists/', views.IncludeArtistListView.as_view(), name='includeartists'),
    path('excludeartists/', views.ExcludeArtistListView.as_view(), name='excludeartists'),
    path('artist/<str:pk>', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('artist/create/', views.ArtistCreate.as_view(), name='artist_create'),
    path('artist/<str:pk>/update', views.ArtistUpdate.as_view(), name='artist_update'),
    # locations
    path('locations/', views.LocationListView.as_view(), name='locations'),
    path('sparselocations/', views.SparseLocationListView.as_view(), name='sparse_locations'),
    path('location/<int:pk>', views.LocationDetailView.as_view(), name='location_detail'),
    path('location/<int:pk>/update', views.LocationUpdateView.as_view(), name='location_update'),
    path('location/create', views.LocationCreate.as_view(), name='location_create'),
    # organisations
    path('sparseorganisation/', views.OrganisationListView.as_view(), name='sparse_organisations'),
    path('sparseorganisation2/', views.OrganisationListView2.as_view(), name='sparse_organisations2'),
    path('organisations/', views.FullOrganisationListView.as_view(), name='organisations'),
    path('organisation/<int:pk>', views.OrganisationDetailView.as_view(), name='organisation_detail'),
    path('organisation/create/', views.OrganisationCreate.as_view(), name='organisation_create'),
    path('organisation/<int:pk>/update/', views.OrganisationUpdate.as_view(), name='organisation_update'),
    path('organisation/<int:pk>/delete/', views.OrganisationDelete.as_view(), name='organisation_delete'),
    # rawvenues
    path('venues/', views.VenueListView.as_view(), name='venues'),
    path('sparsevenues/', views.SparseVenueListView.as_view(), name='sparsevenues'),
    path('venue/<int:pk>', views.VenueDetailView.as_view(), name='venue_detail'),
    path('venue/create/', views.VenueCreate.as_view(), name='venue_create'),
    path('venue/<int:pk>/update/', views.VenueUpdate.as_view(), name='venue_update'),
    path('venue/<int:pk>/delete/', views.VenueDelete.as_view(), name='venue_delete'),
    # concertannouncement
    path('concertannouncements/', views.ConcertAnnouncementListView.as_view(), name='concertannouncements'),
    path('allconcertannouncements/', views.AllConcertAnnouncementListView.as_view(), name='allconcertannouncements'),
    path('concertannouncement/<int:pk>', views.ConcertAnnouncementDetailView.as_view(), name='concertannouncement_detail'),
    path('concertannouncement/create/', views.ConcertAnnouncementCreate.as_view(), name='concertannouncement_create'),
    path('concertannouncement/<int:pk>/update/', views.ConcertAnnouncementUpdate.as_view(), name='concertannouncement_update'),
    path('concertannouncement/<int:pk>/delete/', views.ConcertAnnouncementDelete.as_view(), name='concertannouncement_delete'),
    # relationconcertorganisations
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
    # merge
    path('organisationsmerge/create/', views.OrganisationsMergeCreate.as_view(model=models.OrganisationsMerge), name='organisationsmerge_create'),
    path('organisationsmerge/<str:pk>/confirm/', views.OrganisationsMergeDelete.as_view(model=models.OrganisationsMerge), name='organisationsmerge_delete'),
    path('concertsmerge/create/', views.ConcertsMergeCreate.as_view(model=models.ConcertsMerge), name='concertsmerge_create'),
    path('concertsmerge/<str:pk>/confirm/', views.ConcertsMergeDelete.as_view(model=models.ConcertsMerge), name='concertsmerge_delete')
]
