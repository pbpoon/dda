# Generated by Django 2.1.2 on 2018-11-06 04:47

from django.db import migrations, models
import purchase.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0004_auto_20181105_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='blockcheckinorderitem',
            name='uom',
            field=models.CharField(choices=[('t', '吨'), ('m3', '立方')], default='t', max_length=10, verbose_name='计量单位'),
        ),
        migrations.AlterField(
            model_name='blockcheckinorder',
            name='order',
            field=purchase.fields.OrderField(blank=True, default='New', max_length=20, verbose_name='单号'),
        ),
    ]
