# Generated by Django 2.0.3 on 2018-06-04 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0012_bando_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bando',
            name='slug',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
