# Generated by Django 2.1.2 on 2018-11-26 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0023_auto_20181125_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorderitem',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='数量'),
        ),
    ]
