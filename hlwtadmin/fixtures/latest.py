from pandas import read_excel, isnull
from json import dump, load
from codecs import open

latest = read_excel("latest.xlsx")

fixture = []

country_pk = {}
iso_code_pk = {}
pk_country = {}
with open("citycountries.json", "r", "utf-8") as f:
    for item in load(f):
        if item["model"] == "hlwtadmin.Country":
            key = item["fields"]["iso_code"]
            pk = item["pk"]
            country_pk[pk] = key
            pk_country[key] = pk


location_pk = {}
with open("citycountries.json", "r", "utf-8") as f:
    for item in load(f):
        if item["model"] == "hlwtadmin.Location":
            key = (item["fields"]["city"], country_pk[item["fields"]["country"]])
            value = item["pk"]
            location_pk[key] = value


i = 1
organity_pk = {}
for row in latest[["venue_clean", "stad_clean", "iso_code_clean"]].itertuples():
    venue = row[1]
    city = row[2]
    country = row[3]

    if not isnull(venue) and not isnull(city) and not isnull(country) and (venue, city, country) not in organity_pk:
        try:
            location = location_pk[(city, country)]
        except KeyError:
            location = None

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

gigfinders_pk = {}
with open("gigfinders.json", "r", "utf-8") as f:
    for item in load(f):
        name = item["fields"]["name"]
        if "facebook" in name:
            gigfinders_pk["facebook"] = item["pk"]
        if "bandsintown" in name:
            gigfinders_pk["bandsintown"] = item["pk"]
        if "setlist" in name:
            gigfinders_pk["setlist"] = item["pk"]
        if "songkick" in name:
            gigfinders_pk["songkick"] = item["pk"]
        if "manual" in name:
            gigfinders_pk["manual"] = item["pk"]
        if "podiumfestivalinfo" in name:
            gigfinders_pk["podiumfestivalinfo"] = item["pk"]
        if "datakunstenbe" in name:
            gigfinders_pk["datakunstenbe"] = item["pk"]

i = 1
rawvenue_pk = {}
for row in latest[["venue", "stad", "land", "source", "venue_clean", "stad_clean", "iso_code_clean"]].itertuples():
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
                "raw_venue": key[0:200],
                "raw_location": rloc[0:200],
                "organisation": organity
            }
        }
        rawvenue_pk[key] = i
        fixture.append(data)
        i += 1

genres_pk = {}
with open("genres.json", "r", "utf-8") as f:
    for item in load(f):
        name = item["fields"]["name"]
        genres_pk[name] = item["pk"]


i = 1
musicbrainz_pk = {}
for row in latest[["artiest_mb_naam", "artiest_mb_id", "maingenre"]].itertuples():
    name = row[1]
    mbid = row[2]
    genre = row[3]

    if mbid not in musicbrainz_pk:
        data = {
            "pk": mbid,
            "model": "hlwtadmin.Artist",
            "fields": {
                "name": name,
                "mbid": mbid,
                "genre": [genres_pk[genre]] if not isnull(genre) else []
            }
        }
        musicbrainz_pk[mbid] = mbid
        fixture.append(data)
        i += 1


concert_pk = {}
concert_ids = {}
i = 1
j = 1
k = 1
for row in latest[["titel", "titel_generated", "datum", "last_seen_on", "latitude", "longitude", "cancelled", "ignore", "maingenre", "concert_id", "event_id", "venue_clean", "stad_clean", "iso_code_clean", "artiest_mb_id"]].itertuples():
    title = row[1] if len(str(row[1])) > 5 else row[2]
    created_at = row[4].date()
    concert_id = row[10]
    event_id = row[11]
    genre = row[9]
    organisation = (row[12], row[13], row[14])

    if concert_id not in concert_ids:
        data = {
            "pk": i,
            "model": "hlwtadmin.Concert",
            "fields": {
                "title": str(title)[0:200],
                "date": row[3].date().isoformat(),
                "genre": [genres_pk[genre]] if not isnull(genre) else [],
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
                "latitude": row[5],
                "longitude": row[6],
                "cancelled": row[7],
                "ignore": row[8]
            }
        }
        concert_pk[event_id] = i
        concert_ids[concert_id] = i
        fixture.append(data)
        i += 1

        data = {
            "pk": j,
            "model": "hlwtadmin.RelationConcertOrganisation",
            "fields": {
                "concert": i-1,
                "organisation": organity_pk[organisation] if organisation in organity_pk else None
            }
        }
        fixture.append(data)
        j += 1

        data = {
            "pk": k,
            "model": "hlwtadmin.RelationConcertArtist",
            "fields": {
                "concert": i - 1,
                "artist": row[15]
            }
        }
        fixture.append(data)
        k += 1

    else:
        concert_pk[event_id] = concert_ids[concert_id]

i = 1
concertannouncement_pk = {}
for row in latest[["titel", "titel_generated", "artiest_mb_id", "datum", "source", "artiest", "event_id", "concert_id", "last_seen_on", "venue", "stad", "land", "ignore", "latitude", "longitude"]].itertuples():
    title = row[1] if len(str(row[1])) > 5 else row[2]
    musicbrainz = row[3]
    date = row[4].date()
    created_at = row[9].date()
    gigfinder = gigfinders_pk[row[5]]
    gigfinder_concert_id = row[7].split("_")[-1].strip("setlist").strip("facebook").strip("songkick").strip("bandsintown")
    last_seen_on = row[9].date()
    raw_venue = rawvenue_pk["|".join([str(row[10]), str(row[11]), str(row[12]), str(row[5])])]

    data = {
        "pk": i,
        "model": "hlwtadmin.ConcertAnnouncement",
        "fields": {
            "title": str(title)[0:200],
            "artist": musicbrainz_pk[musicbrainz],
            "date": date.isoformat(),
            "gigfinder": gigfinder,
            "gigfinder_concert_id": gigfinder_concert_id,
            "last_seen_on": last_seen_on.isoformat(),
            "raw_venue": raw_venue,
            "ignore": row[13],
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "latitude": row[14],
            "longitude": row[15],
            "concert": concert_pk[row[7]]
        }
    }
    fixture.append(data)
    concertannouncement_pk[gigfinder_concert_id] = i
    i += 1


k = 1
offset = 0
size = 100000

while (offset) < len(fixture):
    with open("latest_" + str(k) + ".json", "w", "utf-8") as f:
        dump(fixture[offset:(offset+size)], f, indent=4)
    offset += size
    k += 1
