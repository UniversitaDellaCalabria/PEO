# Generated by Django 2.0.3 on 2018-06-04 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_risorse_umane', '0008_auto_20180604_1015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dipendente',
            name='contratto',
        ),
        migrations.AddField(
            model_name='dipendente',
            name='ruolo',
            field=models.CharField(blank=True, default='', max_length=33),
        ),
    ]
