# Generated by Django 2.0.3 on 2019-02-01 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0066_auto_20190131_1654'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='descrizioneindicatore',
            name='univoco',
        ),
        migrations.AddField(
            model_name='descrizioneindicatore',
            name='limite_inserimenti',
            field=models.BooleanField(default=False, help_text='Se attivo, specificare il numero di inserimenti permessi', verbose_name='Limita numero inserimenti'),
        ),
        migrations.AddField(
            model_name='descrizioneindicatore',
            name='numero_inserimenti',
            field=models.IntegerField(default=1, help_text='Numero max inserimenti consentiti', verbose_name='Numero max inserimenti'),
        ),
    ]
