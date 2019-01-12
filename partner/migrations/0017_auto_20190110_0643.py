# Generated by Django 2.1.2 on 2019-01-10 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0016_auto_20190106_1432'),
    ]

    operations = [
        migrations.CreateModel(
            name='MrpSupplier',
            fields=[
            ],
            options={
                'verbose_name': '生产/服务商资料',
                'proxy': True,
                'indexes': [],
            },
            bases=('partner.partner',),
        ),
        migrations.AddField(
            model_name='maininfo',
            name='address_detail',
            field=models.TextField(default=1, verbose_name='详细地址'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='maininfo',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='logo', verbose_name='logo'),
        ),
    ]
