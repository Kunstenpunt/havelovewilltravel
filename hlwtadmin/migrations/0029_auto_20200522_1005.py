# Generated by Django 3.0 on 2020-05-22 08:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0028_auto_20200519_1608'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalIdentifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ExternalIdentifierService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('base_url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='RelationOrganisationIdentifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('start_date_precision', models.PositiveSmallIntegerField(choices=[(2, 'Precise up to the year'), (5, 'Precise up to the month'), (8, 'Precise up to the day')], default=2)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('end_date_precision', models.PositiveSmallIntegerField(choices=[(2, 'Precise up to the year'), (5, 'Precise up to the month'), (8, 'Precise up to the day')], default=2)),
                ('identifier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hlwtadmin.ExternalIdentifier')),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hlwtadmin.Organisation')),
            ],
        ),
        migrations.AddField(
            model_name='externalidentifier',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hlwtadmin.ExternalIdentifierService'),
        ),
    ]
