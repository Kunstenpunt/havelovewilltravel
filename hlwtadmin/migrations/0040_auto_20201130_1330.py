# Generated by Django 3.0.7 on 2020-11-30 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0039_auto_20201130_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='concert',
            name='artist',
            field=models.ManyToManyField(blank=True, default=None, related_name='concert_model', through='hlwtadmin.RelationConcertArtist', to='hlwtadmin.Artist'),
        ),
        migrations.AddField(
            model_name='concert',
            name='organisation',
            field=models.ManyToManyField(blank=True, default=None, related_name='concert_model', through='hlwtadmin.RelationConcertOrganisation', to='hlwtadmin.Organisation'),
        ),
    ]
