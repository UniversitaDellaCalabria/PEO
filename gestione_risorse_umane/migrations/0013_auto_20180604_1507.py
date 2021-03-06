# Generated by Django 2.0.3 on 2018-06-04 13:07

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_risorse_umane', '0012_auto_20180604_1211'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dipendente',
            options={'ordering': ['created'], 'verbose_name': 'Dipendente', 'verbose_name_plural': 'Dipendenti'},
        ),
        migrations.AlterModelOptions(
            name='posizioneeconomica',
            options={'verbose_name': 'Posizione Economica', 'verbose_name_plural': 'Posizioni Economiche'},
        ),
        migrations.AddField(
            model_name='dipendente',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
        migrations.AddField(
            model_name='dipendente',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='livelloposizioneeconomica',
            name='posizione_economica',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gestione_risorse_umane.PosizioneEconomica'),
        ),
    ]
