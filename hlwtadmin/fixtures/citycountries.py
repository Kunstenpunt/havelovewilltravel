from pandas import read_excel, isnull
from json import dump
from codecs import open

latest = read_excel("citycountries.xlsx")

fixture = []

i = 1
country_pk = {}
for country in latest["country"].unique():
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
for location in latest[["name", "country"]].itertuples():
    print(location)
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

with open("citycountries.json", "w", "utf-8") as f:
    dump(fixture, f, indent=4)
