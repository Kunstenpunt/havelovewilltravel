# havelovewilltravel
A data management environment for havelovewilltravel.be

## Data structure

A more complete description of the data structure is provided in the Wiki [https://github.com/Kunstenpunt/havelovewilltravel/wiki].

## Deploy on heroku

- pip freeze > requirements.txt
- 'add "psycopg2-binary==2.7.7" to requirements.txt'

- heroku run python manage.py migrate
- heroku run python manage.py createsuperuser
- heroku run python manage.py loaddata citycountries.json

## Settings
- 'provide api keys and base_urls in /admin for gigfinders'


## Schedule background tasks via Heroku Scheduler
- python manage.py synchronize_with_musicbrainz
- python manage.py synchronze_concerts