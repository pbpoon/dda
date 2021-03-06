# Generated by Django 2.1.2 on 2018-12-14 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0005_invoice_is_paid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='from_order',
            field=models.ManyToManyField(related_name='invoices', to='invoice.OrderInvoiceThrough', verbose_name='对应订单'),
        ),
    ]
