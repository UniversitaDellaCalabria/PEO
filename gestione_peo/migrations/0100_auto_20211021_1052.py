# Generated by Django 2.2.9 on 2021-10-21 08:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0099_bando_agevolazione_modalità'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bando',
            old_name='agevolazione_modalità',
            new_name='agevolazione_modalita',
        ),
    ]