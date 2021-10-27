# Generated by Django 2.2.9 on 2021-10-22 09:27

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_risorse_umane', '0032_merge_20191111_1137'),
        ('gestione_peo', '0107_auto_20211022_0841'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bando',
            name='agevolazione_fatmol',
        ),
        migrations.CreateModel(
            name='Moltiplicatore_Anzianita_Servizio_Bonus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('agevolazione_fatmol', models.IntegerField(default=1, help_text="Fattore di moltiplicazione del punteggio relativo all'anzianità di servizio nel caso di permanenza maggiore o uguale alla soglia stabilita.Serve per agevolare i dipendenti che da N anni non superano la progressione", verbose_name='Fattore moltiplicazione per bonus punteggio anzianità')),
                ('ordinamento', models.PositiveIntegerField(blank=True, default=0, help_text="posizione nell'ordinamento")),
                ('bando', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='gestione_peo.Bando')),
                ('posizione_economica', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestione_risorse_umane.PosizioneEconomica', verbose_name='Categoria')),
            ],
            options={
                'verbose_name': 'Fattore di moltiplicazione per Bonus Anzianità di servizio',
                'verbose_name_plural': 'Fattori di moltiplicazione per Bonus Anzianità di servizio',
            },
        ),
    ]