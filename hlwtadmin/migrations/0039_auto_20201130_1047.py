# Generated by Django 3.0.7 on 2020-11-30 10:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0038_auto_20201130_0958'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='concert',
            name='artist',
        ),
        migrations.RemoveField(
            model_name='concert',
            name='organisation',
        ),
    ]
