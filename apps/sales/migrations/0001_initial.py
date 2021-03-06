# Generated by Django 2.1.7 on 2019-03-13 16:15

from django.db import migrations, models
import public.fields
import public.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SalesOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('draft', '草稿'), ('confirm', '确认'), ('done', '完成'), ('cancel', '取消')], default='draft', max_length=20, verbose_name='状态')),
                ('date', models.DateField(verbose_name='日期')),
                ('created', models.DateField(auto_now_add=True, verbose_name='创建日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order', public.fields.OrderField(db_index=True, default='New', max_length=26, unique=True, verbose_name='订单号码')),
            ],
            options={
                'verbose_name': '销售订单',
                'ordering': ['-date', '-id', '-created'],
                'permissions': (('can_audit', '审核'),),
            },
            bases=(public.models.HasChangedMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SalesOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line', public.fields.LineField(blank=True, verbose_name='行')),
                ('piece', models.IntegerField(blank=True, null=True, verbose_name='件')),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='数量')),
                ('uom', models.CharField(choices=[('t', '吨'), ('m2', '平方')], default='t', max_length=10, verbose_name='计量单位')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='单价')),
            ],
            options={
                'verbose_name': '销售订单行',
                'ordering': ('line',),
            },
            bases=(public.models.OrderItemSaveCreateCommentMixin, models.Model),
        ),
    ]
