# Generated by Django 2.0.3 on 2018-07-24 07:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0018_auto_20180718_1305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rettificadomandabando',
            name='data_rettifica',
        ),
    ]
