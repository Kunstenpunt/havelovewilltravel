# Generated by Django 3.0 on 2020-02-24 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0014_country_iso_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalorganisation',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalorganisation',
            name='annotation',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='historicalorganisation',
            name='capacity',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='annotation',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='capacity',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]