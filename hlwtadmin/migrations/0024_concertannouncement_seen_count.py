# Generated by Django 3.0 on 2020-03-25 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0023_auto_20200323_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name='concertannouncement',
            name='seen_count',
            field=models.IntegerField(default=1),
        ),
    ]
