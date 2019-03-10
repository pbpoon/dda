# Generated by Django 2.1.2 on 2019-03-03 06:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0069_auto_20190123_1752'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inoutorder',
            options={'ordering': ('-date', '-created'), 'verbose_name': '出入库操作'},
        ),
        migrations.AlterModelOptions(
            name='movelocationorder',
            options={'ordering': ('-date', '-created'), 'verbose_name': '移库单'},
        ),
        migrations.AlterModelOptions(
            name='productionorder',
            options={'ordering': ('-date', '-created'), 'verbose_name': '生产订单'},
        ),
        migrations.AlterModelOptions(
            name='turnbackorder',
            options={'ordering': ('-date', '-created'), 'verbose_name': '库存回退'},
        ),
    ]
