# Generated by Django 3.0 on 2020-02-21 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0013_auto_20200208_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='iso_code',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
    ]
