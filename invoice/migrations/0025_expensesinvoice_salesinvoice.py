# Generated by Django 2.1.2 on 2019-01-03 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0024_purchaseinvoice'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpensesInvoice',
            fields=[
            ],
            options={
                'verbose_name': '费用账单',
                'proxy': True,
                'indexes': [],
            },
            bases=('invoice.invoice',),
        ),
        migrations.CreateModel(
            name='SalesInvoice',
            fields=[
            ],
            options={
                'verbose_name': '销售账单',
                'proxy': True,
                'indexes': [],
            },
            bases=('invoice.invoice',),
        ),
    ]
