# Generated by Django 2.1.2 on 2018-12-26 06:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0013_partner_is_invoice'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoicePartner',
            fields=[
            ],
            options={
                'verbose_name': '账单账号',
                'proxy': True,
                'indexes': [],
            },
            bases=('partner.partner',),
        ),
    ]