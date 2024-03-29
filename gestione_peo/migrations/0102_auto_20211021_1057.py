# Generated by Django 2.2.9 on 2021-10-21 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0101_auto_20211021_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bando',
            name='agevolazione_modalita',
            field=models.CharField(choices=[(0, 'Nessuna'), (1, 'Moltiplicazione'), (2, 'Punteggio aggiuntivo')], default=0, help_text="La moltiplicazione prenderà in considerazione il fattore specificato. L'assegnazione del punteggio invece si basa sull'impostazione di PUNTEGGI PER BONUS ANZIANITÀ DI SERVIZIO", max_length=1, verbose_name='Modalità bonus'),
        ),
    ]
