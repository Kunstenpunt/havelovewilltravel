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

## Settings
- 'provide api keys and base_urls in /admin for gigfinders'
- set GOOGLE_PLACES_API_KEY in environment variable
- SET MR_HENRY_API_KEY in environment variable


## Schedule background tasks via Heroku Scheduler
- $ if [ "$(date +%u)" = 4 ]; then python manage.py synchronize_with_musicbrainz; fi # synchronize musicbrainz on thursday evening
- $ if [ "$(date +%u)" -gt 4 ]; then python manage.py synchronize_concerts; fi # synchronize concerts in the weekend, on friday, saturday and sunday evening
- $ python manage.py clean_duplicated_relations
