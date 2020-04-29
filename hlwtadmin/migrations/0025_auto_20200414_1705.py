# Generated by Django 3.0 on 2020-04-14 15:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0024_concertannouncement_seen_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='gigfinderurl',
            name='last_confirmed_by_musicbrainz',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0)),
        ),
        migrations.AddField(
            model_name='gigfinderurl',
            name='last_synchronized',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0)),
        ),
    ]