# Generated by Django 2.1.7 on 2019-03-25 06:03

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_usercollectblock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercollectblock',
            name='block_list',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, null=True), blank=True, null=True, size=None, verbose_name='编号'),
        ),
    ]