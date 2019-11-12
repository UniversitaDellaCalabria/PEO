from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domande_peo', '0029_auto_20191108_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='domandabando',
            name='data_ultima_progressione',
            field=models.DateField(blank=True, null=True, verbose_name='Data presa servizio alla data della presentazione della domanda'),
        ),
        migrations.AlterField(
            model_name='domandabando',
            name='progressione_accettata',
            field=models.BooleanField(default=False, help_text='Marca questa domanda come idonea alla progressione.'),
        ),
    ]
