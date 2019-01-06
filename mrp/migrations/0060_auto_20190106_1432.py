# Generated by Django 2.1.2 on 2019-01-06 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0059_supplier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movelocationorder',
            name='partner',
            field=models.ForeignKey(blank=True, help_text='账单[对方]对应本项。如果为空，则不会生产账单', limit_choices_to={'type__in': 'service'}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.Partner', verbose_name='运输单位'),
        ),
        migrations.AlterField(
            model_name='productionorder',
            name='partner',
            field=models.ForeignKey(default=1, limit_choices_to={'type': 'production'}, on_delete=django.db.models.deletion.CASCADE, to='partner.Partner', verbose_name='生产单位'),
            preserve_default=False,
        ),
    ]
