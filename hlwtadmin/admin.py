from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, ConcertsMerge,\
    OrganisationType, OrganisationsMerge, GigFinder, GigFinderUrl, RelationArtistArtist, RelationConcertOrganisationType, \
    RelationConcertConcertType, RelationArtistArtistType, RelationOrganisationOrganisationType, RelationConcertArtistType, \
    RelationConcertConcert, RelationOrganisationIdentifier, ExternalIdentifier, ExternalIdentifierService, LocationsMerge, \
    RelationLocationLocationType, RelationLocationLocation

# Register your models here.

admin.site.register(ConcertAnnouncement, SimpleHistoryAdmin)

admin.site.register(Artist)

admin.site.register(Concert, SimpleHistoryAdmin)

admin.site.register(Organisation)
admin.site.register(OrganisationType)

admin.site.register(Location, SimpleHistoryAdmin)

admin.site.register(Country, SimpleHistoryAdmin)

admin.site.register(Venue, SimpleHistoryAdmin)

admin.site.register(GigFinderUrl)
admin.site.register(GigFinder, SimpleHistoryAdmin)

admin.site.register(Genre, SimpleHistoryAdmin)

admin.site.register(ExternalIdentifier, SimpleHistoryAdmin)
admin.site.register(ExternalIdentifierService, SimpleHistoryAdmin)

admin.site.register(RelationConcertOrganisation, SimpleHistoryAdmin)
admin.site.register(RelationConcertOrganisationType, SimpleHistoryAdmin)

admin.site.register(RelationConcertArtist, SimpleHistoryAdmin)
admin.site.register(RelationConcertArtistType, SimpleHistoryAdmin)

admin.site.register(RelationOrganisationOrganisation, SimpleHistoryAdmin)
admin.site.register(RelationOrganisationOrganisationType, SimpleHistoryAdmin)

admin.site.register(RelationArtistArtist, SimpleHistoryAdmin)
admin.site.register(RelationArtistArtistType, SimpleHistoryAdmin)

admin.site.register(RelationConcertConcert, SimpleHistoryAdmin)
admin.site.register(RelationConcertConcertType, SimpleHistoryAdmin)

admin.site.register(RelationLocationLocation, SimpleHistoryAdmin)
admin.site.register(RelationLocationLocationType, SimpleHistoryAdmin)

admin.site.register(RelationOrganisationIdentifier, SimpleHistoryAdmin)

admin.site.register(OrganisationsMerge)
admin.site.register(ConcertsMerge)
admin.site.register(LocationsMerge)
