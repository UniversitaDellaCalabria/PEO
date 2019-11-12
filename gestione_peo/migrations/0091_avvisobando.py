# Generated by Django 2.2.7 on 2019-11-11 14:26

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0090_remove_bando_allegato'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvvisoBando',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('titolo', models.CharField(help_text='Titolo clausola (es: Privacy...)', max_length=255)),
                ('corpo_del_testo', models.TextField(help_text='es. Avviso riguardante...')),
                ('ordinamento', models.PositiveIntegerField(blank=True, default=0, help_text="posizione nell'ordinamento")),
                ('allegato', models.FileField(blank=True, null=True, upload_to='avvisi_bando/<django.db.models.fields.related.ForeignKey>/')),
                ('is_active', models.BooleanField(default=True, verbose_name='Visibile agli utenti')),
                ('bando', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestione_peo.Bando')),
            ],
            options={
                'verbose_name': 'Avviso Bando',
                'verbose_name_plural': 'Avvisi Bando',
                'ordering': ('ordinamento',),
            },
        ),
    ]
