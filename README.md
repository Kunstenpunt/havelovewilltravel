# havelovewilltravel
A data management environment for havelovewilltravel.be

## Data structure

A more complete description of the data structure is provided in the Wiki [https://github.com/Kunstenpunt/havelovewilltravel/wiki].

## Deploy on heroku

- pip freeze > requirements.txt
- 'add "psycopg2-binary==2.7.7" to requirements.txt'

- heroku addons:create heroku-postgresql:hobby-basic -a hlwtadmin

- push to github

- heroku run python manage.py migrate -a hlwtadmin
- heroku run python manage.py createsuperuser -a hlwtadmin

## Prepopulate
type citycountries.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type gigfinders.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && - type genres.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && - type organisation_organisation_relation_types.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && - type organisation_types.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_1.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_2.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_3.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_4.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_5.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_6.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_7.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_8.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_9.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json - && type latest_10.json | heroku run --no-tty -a hlwtadmin -- python manage.py loaddata --format=json -

## Settings
- 'provide api keys and base_urls in /admin for gigfinders'
- set GOOGLE_PLACES_API_KEY in environment variable
- SET MR_HENRY_API_KEY in environment variable


## Schedule background tasks via Heroku Scheduler
- python manage.py synchronize_with_musicbrainz
- python manage.py synchronze_concerts