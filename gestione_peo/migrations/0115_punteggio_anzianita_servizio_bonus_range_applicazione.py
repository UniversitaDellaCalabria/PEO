# Generated by Django 2.2.9 on 2021-10-27 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0114_auto_20211027_1649'),
    ]

    operations = [
        migrations.AddField(
            model_name='punteggio_anzianita_servizio_bonus',
            name='range_applicazione',
            field=models.IntegerField(choices=[(0, 'Tutto'), (1, 'Solo periodo attuale permanenza'), (2, 'Solo periodo oltre validità minima')], default=0, help_text='Specifica il range di applicazione del bonus', verbose_name='Applicazione bonus'),
        ),
    ]
