# Generated by Django 2.2.7 on 2019-11-11 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestione_peo', '0088_auto_20191108_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='bando',
            name='allegato',
            field=models.FileField(blank=True, null=True, upload_to='documentazione-bandi/<django.db.models.fields.CharField>/'),
        ),
    ]
