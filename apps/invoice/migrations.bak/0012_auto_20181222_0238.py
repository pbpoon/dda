# Generated by Django 2.1.2 on 2018-12-22 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0011_auto_20181220_0252'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='is_visible',
            field=models.BooleanField(default=True, verbose_name='显示'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='usage',
            field=models.CharField(choices=[('货款', '货款'), ('加工费', '加工费'), ('杂费', '杂费'), ('装车费', '装车费'), ('佣金', '佣金')], default='货款', max_length=20, verbose_name='款项用途'),
        ),
    ]
