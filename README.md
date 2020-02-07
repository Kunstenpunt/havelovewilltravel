# havelovewilltravel
A data management environment for havelovewilltravel.be

## Data structure

## Deploy on heroku

- pip freeze > requirements.txt
- 'add "psycopg2-binary==2.7.7" to requirements.txt'

- heroku run python manage.py migrate
- heroku run python manage.py createsuperuser
- heroku run python manage.py loaddata citycountries.json


## Schedule background tasks via Heroku Scheduler
- python manage.py synchronize_with_musicbrainz
- python manage.py synchronze_concerts