# Generated by Django 2.1.2 on 2018-11-22 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_remove_product_activate'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='activate',
            field=models.BooleanField(default=False, verbose_name='启用'),
        ),
    ]
