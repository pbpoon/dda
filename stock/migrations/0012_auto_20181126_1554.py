# Generated by Django 2.1.2 on 2018-11-26 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0011_auto_20181125_0939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=50, verbose_name='库位名称'),
        ),
    ]
