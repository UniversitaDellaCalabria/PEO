# Generated by Django 2.0.3 on 2018-05-30 07:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gestione_risorse_umane', '0001_initial'),
        ('domande_peo', '0001_initial'),
        ('gestione_peo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='modulodomandabando',
            name='created_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created-domande_peo_modulodomandabando_related+', related_query_name='created-domande_peo_modulodomandabandos+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='modulodomandabando',
            name='descrizione_indicatore',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestione_peo.DescrizioneIndicatore'),
        ),
        migrations.AddField(
            model_name='modulodomandabando',
            name='dipendente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestione_risorse_umane.Dipendente'),
        ),
        migrations.AddField(
            model_name='modulodomandabando',
            name='domanda_bando',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='domande_peo.DomandaBando'),
        ),
        migrations.AddField(
            model_name='modulodomandabando',
            name='modified_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='modified-domande_peo_modulodomandabando_related+', related_query_name='modified-domande_peo_modulodomandabandos+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='domandabando',
            name='bando',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestione_peo.Bando'),
        ),
        migrations.AddField(
            model_name='domandabando',
            name='created_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created-domande_peo_domandabando_related+', related_query_name='created-domande_peo_domandabandos+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='domandabando',
            name='dipendente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestione_risorse_umane.Dipendente'),
        ),
        migrations.AddField(
            model_name='domandabando',
            name='modified_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='modified-domande_peo_domandabando_related+', related_query_name='modified-domande_peo_domandabandos+', to=settings.AUTH_USER_MODEL),
        ),
    ]
