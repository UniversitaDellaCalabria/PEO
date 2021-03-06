# Generated by Django 2.0.3 on 2018-12-14 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0026_auto_20181212_0957'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='modulodomandabando',
            options={'ordering': ['descrizione_indicatore__id_code'], 'verbose_name': 'Modulo compilato Bando del Dipendente', 'verbose_name_plural': 'Moduli compilati Bando dei Dipendenti'},
        ),
        migrations.AlterField(
            model_name='modulodomandabando',
            name='disabilita',
            field=models.BooleanField(default=False, help_text='Se selezionato, esclude il modulo dal calcolo del punteggio'),
        ),
        migrations.AlterField(
            model_name='modulodomandabando',
            name='motivazione',
            field=models.TextField(blank=True, default='', help_text='Motivazione disabilitazione'),
        ),
    ]
