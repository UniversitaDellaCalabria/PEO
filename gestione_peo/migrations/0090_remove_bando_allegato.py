# Generated by Django 2.2.7 on 2019-11-11 14:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0089_bando_allegato'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bando',
            name='allegato',
        ),
    ]
