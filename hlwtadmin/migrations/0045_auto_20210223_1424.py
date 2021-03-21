# Generated by Django 3.0.7 on 2021-02-23 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0044_gigfinderurl_ignore_periods'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gigfinderurl',
            name='ignore_periods',
        ),
        migrations.AddField(
            model_name='gigfinderurl',
            name='ignore_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gigfinderurl',
            name='ignore_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
