from django.contrib import admin

from .models import Concert, ConcertAnnouncement, Artist, Organisation, Location, \
    Country, RelationOrganisationOrganisation, RelationConcertArtist, RelationConcertOrganisation, Venue, OrganisationType

from simple_history.admin import SimpleHistoryAdmin

# Register your models here.

admin.site.register(Concert, SimpleHistoryAdmin)
admin.site.register(ConcertAnnouncement)
admin.site.register(Artist)
admin.site.register(Organisation, SimpleHistoryAdmin)
admin.site.register(Location)
admin.site.register(Country)
admin.site.register(RelationConcertOrganisation, SimpleHistoryAdmin)
admin.site.register(RelationOrganisationOrganisation, SimpleHistoryAdmin)
admin.site.register(RelationConcertArtist, SimpleHistoryAdmin)
admin.site.register(Venue)
admin.site.register(OrganisationType)
