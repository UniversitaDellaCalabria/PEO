# Generated by Django 2.0.3 on 2018-11-16 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0024_domandabando_punteggio_anzianita_manuale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domandabando',
            name='punteggio_anzianita_manuale',
            field=models.FloatField(blank=True, help_text='impostato manualmente', null=True, verbose_name="Punteggio assegnato all'anzianità interna MANUALE"),
        ),
    ]
