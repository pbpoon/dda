# Generated by Django 2.1.2 on 2018-11-01 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0019_auto_20181101_0559'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaseorder',
            options={'ordering': ['-order'], 'verbose_name': '采购订单'},
        ),
    ]
