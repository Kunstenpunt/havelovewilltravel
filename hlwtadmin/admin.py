from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, ConcertsMerge,\
    OrganisationType, OrganisationsMerge, GigFinder, GigFinderUrl, RelationArtistArtist, RelationConcertOrganisationType, \
    RelationConcertConcertType, RelationArtistArtistType, RelationOrganisationOrganisationType, RelationConcertArtistType, \
    RelationConcertConcert, RelationOrganisationIdentifier, ExternalIdentifier, ExternalIdentifierService, LocationsMerge, \
    RelationLocationLocationType, RelationLocationLocation


# Define the admin class
class ArtistAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_filter = ["genre"]


class ConcertAnnouncementAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["artist", "concert", "raw_venue"]
    list_filter = ["date", "until_date"]
    search_fields = ["artist__name"]


class VenueAdmin(SimpleHistoryAdmin):
    search_fields = ["raw_venue"]
    autocomplete_fields = ["organisation"]


class RelationConcertArtistInline(admin.TabularInline):
    model = RelationConcertArtist
    autocomplete_fields = ["concert", "artist"]


class RelationConcertOrganisationInline(admin.TabularInline):
    model = RelationConcertOrganisation
    autocomplete_fields = ["concert", "organisation"]


class ConcertAdmin(SimpleHistoryAdmin):
    search_fields = ["title", "relationconcertartist__artist__name", "relationconcertorganisation__organisation__name"]
    list_filter = ["date", "genre"]
    inlines = [RelationConcertArtistInline, RelationConcertOrganisationInline]


class OrganisationAdmin(SimpleHistoryAdmin):
    search_fields = ["name"]
    autocomplete_fields = ['location']


class LocationAdmin(SimpleHistoryAdmin):
    search_fields = ["city", "country__name"]
    autocomplete_fields = ["country"]
    list_filter = ["country__name"]


class CountryAdmin(SimpleHistoryAdmin):
    search_fields = ["name"]


class ExternalIdentifierAdmin(SimpleHistoryAdmin):
    search_fields = ["identifier"]


class RelationConcertArtistAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["artist", "concert"]
    search_fields = ["artist__name"]


class RelationConcertOrganisationAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["concert", "organisation"]
    search_fields = ["organisation__name"]


class RelationOrganisationOrganisationAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["organisation_a", "organisation_b"]


class RelationArtistArtistAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["artist_a", "artist_b"]


class RelationConcertConcertAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["concert_a", "concert_b"]


class RelationLocationLocationAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["location_a", "location_b"]


class RelationOrganisationIdentifierAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["organisation", "identifier"]


# Register your models here.
admin.site.register(ConcertAnnouncement, ConcertAnnouncementAdmin)

admin.site.register(Artist, ArtistAdmin)

admin.site.register(Concert, ConcertAdmin)

admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationType)

admin.site.register(Location, LocationAdmin)

admin.site.register(Country, CountryAdmin)

admin.site.register(Venue, VenueAdmin)

admin.site.register(GigFinderUrl)
admin.site.register(GigFinder, SimpleHistoryAdmin)

admin.site.register(Genre, SimpleHistoryAdmin)

admin.site.register(ExternalIdentifier, ExternalIdentifierAdmin)
admin.site.register(ExternalIdentifierService, SimpleHistoryAdmin)

admin.site.register(RelationConcertOrganisation, RelationConcertOrganisationAdmin)
admin.site.register(RelationConcertOrganisationType, SimpleHistoryAdmin)

admin.site.register(RelationConcertArtist, RelationConcertArtistAdmin)
admin.site.register(RelationConcertArtistType, SimpleHistoryAdmin)

admin.site.register(RelationOrganisationOrganisation, RelationOrganisationOrganisationAdmin)
admin.site.register(RelationOrganisationOrganisationType, SimpleHistoryAdmin)

admin.site.register(RelationArtistArtist, RelationArtistArtistAdmin)
admin.site.register(RelationArtistArtistType, SimpleHistoryAdmin)

admin.site.register(RelationConcertConcert, RelationConcertConcertAdmin)
admin.site.register(RelationConcertConcertType, SimpleHistoryAdmin)

admin.site.register(RelationLocationLocation, RelationLocationLocationAdmin)
admin.site.register(RelationLocationLocationType, SimpleHistoryAdmin)

admin.site.register(RelationOrganisationIdentifier, RelationOrganisationIdentifierAdmin)

admin.site.register(OrganisationsMerge)
admin.site.register(ConcertsMerge)
admin.site.register(LocationsMerge)
