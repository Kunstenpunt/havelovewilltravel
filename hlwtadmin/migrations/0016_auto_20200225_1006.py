# Generated by Django 3.0 on 2020-02-25 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0015_auto_20200224_1447'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalorganisation',
            name='active',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalorganisation',
            name='verified',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='active',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='verified',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
