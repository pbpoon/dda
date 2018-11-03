# Generated by Django 2.1.2 on 2018-10-31 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0009_auto_20181031_0610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorder',
            name='state',
            field=models.CharField(choices=[('draft', '草稿'), ('confirm', '确认'), ('cancel', '取消')], default='draft', max_length=20, verbose_name='状态'),
        ),
    ]
