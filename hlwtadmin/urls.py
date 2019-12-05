from django.urls import path
from . import views, models

urlpatterns = [
    path('', views.index, name='index'),
    # concerts
    path('concerts/', views.ConcertListView.as_view(), name='concerts'),
    path('venueless_concerts/', views.VenuelessConcertListView.as_view(), name='venueless_concerts'),
    path('artistless_concerts/', views.ArtistlessConcertListView.as_view(), name='artistless_concerts'),
    path('concert/<int:pk>', views.ConcertDetailView.as_view(), name='concert_detail'),
    path('concert/create/', views.ConcertCreate.as_view(), name='concert_create'),
    path('concert/<int:pk>/update/', views.ConcertUpdate.as_view(), name='concert_update'),
    path('concert/<int:pk>/delete/', views.ConcertDelete.as_view(), name='concert_delete'),
    # concerts
    path('artists/', views.MusicbrainzListView.as_view(), name='artists'),
    path('artist/<int:pk>', views.MusicbrainzDetailView.as_view(), name='artist_detail'),
    # organities
    path('sparseorganities/', views.OrganityListView.as_view(), name='sparse_organities'),
    path('organities/', views.FullOrganityListView.as_view(), name='organities'),
    path('organity/<int:pk>', views.OrganityDetailView.as_view(), name='organity_detail'),
    path('organity/create/', views.OrganityCreate.as_view(), name='organity_create'),
    path('organity/<int:pk>/update/', views.OrganityUpdate.as_view(), name='organity_update'),
    path('organity/<int:pk>/delete/', views.OrganityDelete.as_view(), name='organity_delete'),
    # rawvenues
    path('rawvenues/', views.RawvenueListView.as_view(), name='rawvenues'),
    path('rawvenue/<int:pk>', views.RawvenueDetailView.as_view(), name='rawvenue_detail'),
    path('rawvenue/create/', views.RawvenueCreate.as_view(), name='rawvenue_create'),
    path('rawvenue/<int:pk>/update/', views.RawvenueUpdate.as_view(), name='rawvenue_update'),
    path('rawvenue/<int:pk>/delete/', views.RawvenueDelete.as_view(), name='rawvenue_delete'),
    # concertannouncement
    path('concertannouncements/', views.ConcertAnnouncementListView.as_view(), name='concertannouncements'),
    path('concertannouncement/<int:pk>', views.ConcertAnnouncementDetailView.as_view(), name='concertannouncement_detail'),
    path('concertannouncement/create/', views.ConcertAnnouncementCreate.as_view(), name='concertannouncement_create'),
    path('concertannouncement/<int:pk>/update/', views.ConcertAnnouncementUpdate.as_view(), name='concertannouncement_update'),
    path('concertannouncement/<int:pk>/delete/', views.ConcertAnnouncementDelete.as_view(), name='concertannouncement_delete'),
    # relationconcertorganities
    path('relationconcertorganity/create/<int:pk>', views.RelationConcertOrganityCreate.as_view(), name='relationconcertorganity_create'),
    path('relationconcertorganity/<int:pk>/update/', views.RelationConcertOrganityUpdate.as_view(), name='relationconcertorganity_update'),
    path('relationconcertorganity/<int:pk>/delete/', views.RelationConcertOrganityDelete.as_view(), name='relationconcertorganity_delete'),
    # relationconcertorganities
    path('relationconcertmusicbrainz/create/<int:pk>', views.RelationConcertMusicbrainzCreate.as_view(), name='relationconcertmusicbrainz_create'),
    path('relationconcertmusicbrainz/<int:pk>/update/', views.RelationConcertMusicbrainzUpdate.as_view(), name='relationconcertmusicbrainz_update'),
    path('relationconcertmusicbrainz/<int:pk>/delete/', views.RelationConcertMusicbrainzDelete.as_view(), name='relationconcertmusicbrainz_delete'),
    # autocompletes
    path('musicbrainz-autocomplete/', views.MusicbrainzAutocomplete.as_view(model=models.Musicbrainz), name='musicbrainz_autocomplete'),
    path('concert-autocomplete/', views.ConcertAutocomplete.as_view(model=models.Concert), name='concert_autocomplete'),
    path('organity-autocomplete/', views.OrganityAutocomplete.as_view(model=models.Organity), name='organity_autocomplete'),
]