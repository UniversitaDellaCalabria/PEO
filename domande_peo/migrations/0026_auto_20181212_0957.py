# Generated by Django 2.0.3 on 2018-12-12 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0025_auto_20181116_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='modulodomandabando',
            name='disabilita',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='modulodomandabando',
            name='motivazione',
            field=models.TextField(blank=True, default=''),
        ),
    ]
