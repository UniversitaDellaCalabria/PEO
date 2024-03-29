# Generated by Django 2.2.9 on 2021-10-21 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0100_auto_20211021_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bando',
            name='agevolazione_fatmol',
            field=models.IntegerField(default=1, help_text="Fattore di moltiplicazione del punteggio relativo all'anzianità di servizio nel caso di permanenza maggiore o uguale alla soglia stabilita.Serve per agevolare i dipendenti che da N anni non superano la progressione", verbose_name='Fattore moltiplicazione per bonus punteggio anzianità'),
        ),
    ]
