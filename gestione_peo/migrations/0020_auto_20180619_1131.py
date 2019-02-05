# Generated by Django 2.0.3 on 2018-06-19 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0019_auto_20180614_1006'),
    ]

    operations = [
        migrations.AddField(
            model_name='bando',
            name='data_validita_titoli_fine',
            field=models.DateField(default='2018-01-01', help_text='Data fino alla quale i titoli sono accettati'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bando',
            name='data_validita_titoli_inizio',
            field=models.DateField(default='2018-01-01', help_text='Data a partire dalla quale i titoli sono accettati'),
            preserve_default=False,
        ),
    ]
