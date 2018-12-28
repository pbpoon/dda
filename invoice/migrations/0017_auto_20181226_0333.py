# Generated by Django 2.1.2 on 2018-12-26 03:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0016_auto_20181224_0506'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoiceduedatedefaultset',
            options={'verbose_name': '订单账单限期默认设置'},
        ),
        migrations.AlterField(
            model_name='invoice',
            name='state',
            field=models.CharField(choices=[('draft', '草稿'), ('confirm', '确认'), ('cancel', '取消'), ('done', '完成')], default='draft', max_length=10, verbose_name='状态'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='usage',
            field=models.CharField(choices=[('货款', '货款'), ('加工费', '加工费'), ('杂费', '杂费'), ('运输费', '运输费'), ('装车费', '装车费'), ('佣金', '佣金')], default='货款', max_length=20, verbose_name='款项用途'),
        ),
        migrations.AlterField(
            model_name='invoiceduedatedefaultset',
            name='updated',
            field=models.DateField(auto_now=True, verbose_name='更新日期'),
        ),
    ]
