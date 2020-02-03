from django.contrib import admin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, OrganisationType

# Register your models here.

admin.site.register(Concert)
admin.site.register(ConcertAnnouncement)
admin.site.register(Artist)
admin.site.register(Organisation)
admin.site.register(Location)
admin.site.register(Country)
admin.site.register(RelationConcertOrganisation)
admin.site.register(RelationOrganisationOrganisation)
admin.site.register(RelationConcertArtist)
admin.site.register(Venue)
admin.site.register(OrganisationType)
