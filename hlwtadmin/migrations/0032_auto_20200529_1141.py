# Generated by Django 3.0 on 2020-05-29 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hlwtadmin', '0031_auto_20200529_0952'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationLocationLocationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AlterModelOptions(
            name='organisation',
            options={'ordering': ['sort_name']},
        ),
        migrations.CreateModel(
            name='RelationLocationLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_a', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='locationa', to='hlwtadmin.Location')),
                ('location_b', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='locationb', to='hlwtadmin.Location')),
                ('relation_type', models.ManyToManyField(blank=True, to='hlwtadmin.RelationLocationLocationType')),
            ],
        ),
    ]