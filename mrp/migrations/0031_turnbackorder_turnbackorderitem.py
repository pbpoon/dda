# Generated by Django 2.1.2 on 2018-12-12 14:03

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import public.fields


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0032_auto_20181212_0152'),
        ('stock', '0013_auto_20181212_0305'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mrp', '0030_auto_20181211_1504'),
    ]

    operations = [
        migrations.CreateModel(
            name='TurnBackOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('reason', models.CharField(max_length=80, verbose_name='原因')),
                ('order', public.fields.OrderField(blank=True, default='New', max_length=20, verbose_name='单号')),
                ('date', models.DateField(default=datetime.datetime.now, verbose_name='日期')),
                ('created', models.DateField(auto_now_add=True, verbose_name='创建日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turnbackorder_entry', to=settings.AUTH_USER_MODEL, verbose_name='登记人')),
                ('handler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turnbackorder_handler', to=settings.AUTH_USER_MODEL, verbose_name='经办人')),
                ('warehouse', models.ForeignKey(blank=True, help_text='如果没有指定，将会按原单出库仓库接受', null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Warehouse', verbose_name='接收仓库')),
            ],
            options={
                'verbose_name': '出入库操作',
            },
        ),
        migrations.CreateModel(
            name='TurnBackOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line', public.fields.LineField(blank=True, verbose_name='行')),
                ('piece', models.IntegerField(default=1, verbose_name='件')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='数量')),
                ('uom', models.CharField(choices=[('t', '吨'), ('m3', '立方'), ('m2', '平方')], default='t', max_length=10, verbose_name='计量单位')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='turnbackorderitem_location', to='stock.Location', verbose_name='库位')),
                ('location_dest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='turnbackorderitem_location_dest', to='stock.Location', verbose_name='目标库位')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='mrp.TurnBackOrder', verbose_name='对应订单')),
                ('package_list', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.PackageList', verbose_name='码单')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product', verbose_name='product')),
            ],
            options={
                'verbose_name': '出入库操作明细行',
            },
        ),
    ]