# Generated by Django 2.0.3 on 2018-11-15 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0023_auto_20180804_0100'),
    ]

    operations = [
        migrations.AddField(
            model_name='domandabando',
            name='punteggio_anzianita_manuale',
            field=models.FloatField(blank=True, help_text='impostato manualmente', null=True),
        ),
    ]
