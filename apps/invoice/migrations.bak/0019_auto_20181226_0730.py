# Generated by Django 2.1.2 on 2018-12-26 07:30

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0018_remove_invoice_is_paid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='due_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='到期日'),
            preserve_default=False,
        ),
    ]
