# Generated by Django 2.1.2 on 2018-11-01 05:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_auto_20181101_0453'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='block_uom',
            new_name='uom',
        ),
    ]
