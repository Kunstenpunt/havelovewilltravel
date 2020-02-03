from pandas import read_excel, isnull
from json import dump
from codecs import open

latest = read_excel("latest.xlsx")

fixture = []

i = 1
country_pk = {}
for country in latest["land_clean"].unique():
    if not isnull(country):
        data = {
            "pk": i,
            "model": "hlwtadmin.Country",
            "fields": {
                "name": country
            }
        }
        country_pk[country] = i
        i += 1

        fixture.append(data)


i = 1
location_pk = {}
for location in latest[["stad_clean", "land_clean"]].itertuples():
    city = location[1]
    country = location[2]
    if not isnull(city) and not isnull(country) and (city, country) not in location_pk:
        data = {
            "pk": i,
            "model": "hlwtadmin.Location",
            "fields": {
                "city": city,
                "country": country_pk[country]
            }
        }
        location_pk[(city, country)] = i
        i += 1
        fixture.append(data)

fixture.append(
    {
        "pk": 1,
        "model": "hlwtadmin.OrganisationType",
        "fields": {
            "name": "Venue"
        }
    }
)

i = 1
organity_pk = {}
for row in latest[["venue_clean", "stad_clean", "land_clean"]].itertuples():
    venue = row[1]
    city = row[2]
    country = row[3]

    if not isnull(venue) and not isnull(city) and not isnull(country) and (venue, city, country) not in organity_pk:
        location = location_pk[(city, country)]

        data = {
            "pk": i,
            "model": "hlwtadmin.Organisation",
            "fields": {
                "name": venue,
                "location": location,
                "organisation_type": [1]

            }
        }
        organity_pk[(venue, city, country)] = i

        fixture.append(data)

        i += 1

i = 1
rawvenue_pk = {}
for row in latest[["venue", "stad", "land", "source", "venue_clean", "stad_clean", "land_clean"]].itertuples():
    rawvenue = row[1]
    rawcity = row[2]
    rawcountry = row[3]
    source = row[4]

    organity = organity_pk[(row[5], row[6], row[7])] if (row[5], row[6], row[7]) in organity_pk else None

    key = "|".join([str(rawvenue), str(rawcity), str(rawcountry), str(source)])
    rloc = "|".join([str(rawcity), str(rawcountry), str(source)])

    if key not in rawvenue_pk:
        data = {
            "pk": i,
            "model": "hlwtadmin.Venue",
            "fields": {
                "raw_venue": key,
                "raw_location": rloc,
                "venue": organity
            }
        }
        rawvenue_pk[key] = i
        fixture.append(data)
        i += 1

i = 1
musicbrainz_pk = {}
for row in latest[["artiest_mb_naam", "artiest_mb_id"]].itertuples():
    name = row[1]
    mbid = row[2]

    if mbid not in musicbrainz_pk:
        data = {
            "pk": i,
            "model": "hlwtadmin.Artist",
            "fields": {
                "name": name,
                "mbid": mbid
            }
        }
        musicbrainz_pk[mbid] = i
        fixture.append(data)
        i += 1

# i = 1
# concert_pk = {}
# for row in latest[["concert_id", "titel", "titel_generated", "datum", "cancelled"]].itertuples():
#     cid = row[1]
#     title = row[2] if len(str(row[1])) > 3 else row[3]
#     date = row[4]
#     cancelled = row[5]
#
#     if cid not in concert_pk:
#         data = {
#             "pk": i,
#             "model": "hlwtadmin.Concert",
#             "fields": {
#                 "title": title,
#                 "date": date.date().isoformat(),
#                 "cancelled": cancelled
#             }
#         }
#         concert_pk[cid] = i
#         fixture.append(data)
#         i += 1

concertorganitytype = ["At festival", "In venue"]
for i, gf in enumerate(concertorganitytype):
    data = {
        "pk": i + 1,
        "model": "hlwtadmin.RelationConcertOrganisationType",
        "fields": {
            "name": gf
        }
    }
    fixture.append(data)

# i = 1
# concertannouncement_pk = {}
# for row in latest[["titel", "titel_generated", "artiest_mb_id", "datum", "source", "artiest", "event_id", "concert_id", "last_seen_on", "venue", "stad", "land", "ignore"]].itertuples():
#     title = row[1] if len(str(row[1])) > 3 else row[2]
#     musicbrainz = row[3]
#     date = row[4].date()
#     gigfinder = gigfinders.index(row[5]) + 1
#     gigfinder_artist_name = row[6]
#     gigfinder_concert_id = row[7]
#     concert = concert_pk[row[8]] if not isnull(row[8]) else None
#     last_seen_on = row[9].date()
#     raw_venue = rawvenue_pk["|".join([str(row[10]), str(row[11]), str(row[12]), str(row[5])])]
#
#     if gigfinder_concert_id not in concertannouncement_pk:
#         data = {
#             "pk": i,
#             "model": "hlwtadmin.ConcertAnnouncement",
#             "fields": {
#                 "title": title,
#                 "musicbrainz": musicbrainz_pk[musicbrainz],
#                 "date": date.isoformat(),
#                 "gigfinder": gigfinder,
#                 "gigfinder_artist_name": gigfinder_artist_name,
#                 "gigfinder_concert_id": gigfinder_concert_id,
#                 "concert": concert,
#                 "last_seen_on": last_seen_on.isoformat(),
#                 "raw_venue": raw_venue,
#                 "ignore": row[13]
#             }
#         }
#         fixture.append(data)
#         concertannouncement_pk[gigfinder_concert_id] = i
#         i += 1
#
# i = 1
# relationconcertmb_pk = {}
# for row in latest[["concert_id", "artiest_mb_id"]].itertuples():
#     cid = row[1]
#     musicbrainz = row[2]
#     if (cid, musicbrainz) not in relationconcertmb_pk and cid in concert_pk and musicbrainz in musicbrainz_pk:
#         data = {
#             "pk": i,
#             "model": "hlwtadmin.RelationConcertMusicbrainz",
#             "fields": {
#                 "concert": concert_pk[cid],
#                 "musicbrainz": musicbrainz_pk[musicbrainz]
#             }
#         }
#         fixture.append(data)
#         relationconcertmb_pk[(cid, musicbrainz)] = i
#         i += 1
#
# i = 1
# relationconcertorganity_pk = {}
# for row in latest[["concert_id", "venue_clean", "stad_clean", "land_clean"]].itertuples():
#     cid = row[1]
#     organity = (row[2], row[3], row[4])
#
#     if (cid, organity) not in relationconcertorganity_pk and cid in concert_pk and organity in organity_pk:
#         data = {
#             "pk": i,
#             "model": "hlwtadmin.RelationConcertOrganity",
#             "fields": {
#                 "concert": concert_pk[cid],
#                 "organity": organity_pk[organity],
#                 "organity_credited_as": ", ".join(organity),
#                 "relation_type": [2]
#             }
#         }
#         fixture.append(data)
#         relationconcertorganity_pk[(cid, organity)] = i
#         i += 1

with open("latest.json", "w", "utf-8") as f:
    dump(fixture, f, indent=4)
