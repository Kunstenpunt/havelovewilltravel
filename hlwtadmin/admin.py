from django.contrib import admin

from .models import Concert, ConcertAnnouncement, Musicbrainz, Gigfinder, GigfinderUrl, Organity, Address, Location, \
    Country, RelationOrganityOrganity, RelationConcertMusicbrainz, RelationConcertOrganity, RawVenue, OrganityType

# Register your models here.

admin.site.register(Concert)
admin.site.register(ConcertAnnouncement)
admin.site.register(Musicbrainz)
admin.site.register(GigfinderUrl)
admin.site.register(Gigfinder)
admin.site.register(Organity)
admin.site.register(Address)
admin.site.register(Location)
admin.site.register(Country)
admin.site.register(RelationConcertOrganity)
admin.site.register(RelationOrganityOrganity)
admin.site.register(RelationConcertMusicbrainz)
admin.site.register(RawVenue)
admin.site.register(OrganityType)
