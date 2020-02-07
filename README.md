# havelovewilltravel
A data management environment for havelovewilltravel.be

## Data structure

## Deploy

python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata citycountries.json


## Background tasks
python manage.py synchronize_with_musicbrainz
python manage.py synchronze_concerts