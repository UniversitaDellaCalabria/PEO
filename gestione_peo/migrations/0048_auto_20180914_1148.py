# Generated by Django 2.0.3 on 2018-09-14 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0047_bando_priorita_titoli_studio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bando',
            name='priorita_titoli_studio',
            field=models.BooleanField(default=True, help_text='Se attivo, nel calcolo del punteggio, verrà valutata solo la categoria di titoli di studio più elevata. (Es: laurea magistrale > laurea triennale)', verbose_name='Valuta solo titolo di studio più elevato'),
        ),
    ]
