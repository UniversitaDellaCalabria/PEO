# Generated by Django 2.2.9 on 2021-10-26 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0109_auto_20211026_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='moltiplicatore_anzianita_servizio_bonus',
            name='moltiplica_tutto',
            field=models.BooleanField(default=True, help_text='Se True moltiplica tutto il punteggio calcolato, altrimenti moltiplica solo il punteggio assegnato agli anni oltre la permanenza minima', verbose_name='Moltiplica tutto il punteggio'),
        ),
    ]
