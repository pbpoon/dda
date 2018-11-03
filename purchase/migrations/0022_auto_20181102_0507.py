# Generated by Django 2.1.2 on 2018-11-02 05:07

from django.db import migrations
import purchase.fields


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0021_auto_20181102_0505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorder',
            name='order',
            field=purchase.fields.OrderField(db_index=True, default='New', max_length=10, unique=True, verbose_name='订单号码'),
        ),
    ]
