# Generated by Django 2.1.2 on 2019-01-03 07:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0014_invoicepartner'),
        ('sales', '0011_auto_20181219_0249'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('partner.partner',),
        ),
        migrations.AlterField(
            model_name='salesorder',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Customer', verbose_name='客户名称'),
        ),
    ]