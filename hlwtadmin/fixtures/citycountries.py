from pandas import read_excel, isnull
from json import dump
from codecs import open
from sys import argv

latest = read_excel("citycountries.xlsx")
filename = "citycountries.json"

if len(argv) == 2 and argv[1] == "test":
    latest = latest[latest["test"] == True]
    filename = "citycountries_test.json"

fixture = []

i = 1
country_pk = {}
for country in latest["country"].unique():
    if not isnull(country):
        data = {
            "pk": i,
            "model": "hlwtadmin.Country",
            "fields": {
                "name": country,
                "iso_code": latest[latest["country"] == country]["iso_code"].values[0].lower() if not isnull(latest[latest["country"] == country]["iso_code"].values[0]) else "NA"
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

with open(filename, "w", "utf-8") as f:
    dump(fixture, f, indent=4)
