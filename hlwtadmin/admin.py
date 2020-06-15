from django.contrib import admin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, Genre, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, ConcertsMerge,\
    OrganisationType, OrganisationsMerge, GigFinder, GigFinderUrl, RelationArtistArtist, RelationConcertOrganisationType, \
    RelationConcertConcertType, RelationArtistArtistType, RelationOrganisationOrganisationType, RelationConcertArtistType, \
    RelationConcertConcert, RelationOrganisationIdentifier, ExternalIdentifier, ExternalIdentifierService, LocationsMerge, \
    RelationLocationLocationType, RelationLocationLocation

# Register your models here.

admin.site.register(ConcertAnnouncement)

admin.site.register(Artist)

admin.site.register(OrganisationType)

admin.site.register(Location)
admin.site.register(Country)

admin.site.register(Venue)

admin.site.register(GigFinderUrl)
admin.site.register(GigFinder)

admin.site.register(Genre)

admin.site.register(ExternalIdentifier)
admin.site.register(ExternalIdentifierService)

admin.site.register(RelationConcertOrganisationType)

admin.site.register(RelationConcertArtistType)

admin.site.register(RelationOrganisationOrganisationType)

admin.site.register(RelationArtistArtist)
admin.site.register(RelationArtistArtistType)

admin.site.register(RelationConcertConcert)
admin.site.register(RelationConcertConcertType)

admin.site.register(RelationLocationLocation)
admin.site.register(RelationLocationLocationType)

admin.site.register(RelationOrganisationIdentifier)

admin.site.register(OrganisationsMerge)
admin.site.register(ConcertsMerge)
admin.site.register(LocationsMerge)
