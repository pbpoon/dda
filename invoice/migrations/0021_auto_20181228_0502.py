# Generated by Django 2.1.2 on 2018-12-28 05:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0020_auto_20181228_0448'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoiceitem',
            name='purchase_order_item',
        ),
        migrations.RemoveField(
            model_name='invoiceitem',
            name='sales_order_item',
        ),
    ]