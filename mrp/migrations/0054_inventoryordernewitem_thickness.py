# Generated by Django 2.1.2 on 2018-12-18 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0053_auto_20181217_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryordernewitem',
            name='thickness',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='厚度规格'),
        ),
    ]
