# Generated by Django 2.0.3 on 2018-06-27 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0023_auto_20180620_0910'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='descrizioneindicatore',
            options={'ordering': ['indicatore_ponderato', 'ordinamento'], 'verbose_name': 'Descrizione Indicatore', 'verbose_name_plural': 'Descrizioni Indicatori'},
        ),
        migrations.AlterModelOptions(
            name='indicatoreponderato',
            options={'ordering': ['ordinamento'], 'verbose_name': 'Indicatore Ponderato', 'verbose_name_plural': 'Indicatori Ponderati'},
        ),
        migrations.RemoveField(
            model_name='bando',
            name='data_validita_titoli_inizio',
        ),
        migrations.AlterField(
            model_name='moduloinserimentocampi',
            name='tipo',
            field=models.CharField(choices=[('CharField', 'caratteri'), ('TextField', 'descrizione lunga'), ('IntegerField', 'numero intero'), ('FloatField', 'numero con virgola'), ('_TitoloStudioField', 'selezione titolo di studio'), ('DateField', 'data'), ('StartDateField', 'data inizio'), ('EndDateField', 'data fine + checkbox "fino ad oggi"'), ('FileField', 'allegato pdf'), ('CheckBoxField', 'checkbox'), ('CustomSelectBoxField', 'menu a tendina'), ('CustomRadioBoxField', 'serie di opzioni'), ('ProtocolloForteField', 'protocollo FORTE (numero + data)'), ('ProtocolloDeboleField', 'protocollo DEBOLE (numero + data)')], max_length=33),
        ),
        migrations.AlterField(
            model_name='moduloinserimentocampi',
            name='valore',
            field=models.CharField(blank=True, default='', help_text="compilare esclusivamente se si sceglie 'Menu a tendina' oppure 'Serie di Opzioni'", max_length=255, verbose_name='Lista di Valori'),
        ),
    ]
