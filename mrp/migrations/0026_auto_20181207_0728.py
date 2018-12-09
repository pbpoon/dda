# Generated by Django 2.1.2 on 2018-12-07 07:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import public.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0012_auto_20181126_1554'),
        ('sales', '0006_remove_salesorder_warehouse'),
        ('partner', '0004_auto_20181125_0544'),
        ('purchase', '0025_auto_20181203_0646'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('product', '0030_auto_20181206_0719'),
        ('mrp', '0025_auto_20181205_0011'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expenses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('expense_by_uom', models.CharField(choices=[('part', '夹数'), ('quantity', '数量(t/m3/m2)'), ('one', '次/个/车')], max_length=20, verbose_name='计费单位')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': '费用明细',
            },
        ),
        migrations.CreateModel(
            name='ExpensesItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='费用名称')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='单价')),
                ('uom_name', models.CharField(max_length=10, verbose_name='单位')),
            ],
            options={
                'verbose_name': '费用名称',
            },
        ),
        migrations.CreateModel(
            name='InOutOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('draft', '草稿'), ('confirm', '确认'), ('done', '完成'), ('cancel', '取消')], default='draft', max_length=20, verbose_name='状态')),
                ('date', models.DateField(verbose_name='日期')),
                ('created', models.DateField(auto_now_add=True, verbose_name='创建日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('type', models.CharField(choices=[('in', '入库'), ('out', '出库')], max_length=10, verbose_name='出入库类型')),
                ('order', public.fields.OrderField(blank=True, default='New', max_length=20, verbose_name='单号')),
                ('counter', models.IntegerField(blank=True, null=True, verbose_name='货柜数')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inoutorder_entry', to=settings.AUTH_USER_MODEL, verbose_name='登记人')),
                ('handler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inoutorder_handler', to=settings.AUTH_USER_MODEL, verbose_name='经办人')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inoutorder_location', to='stock.Location', verbose_name='原库位')),
                ('location_dest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inoutorder_location_dest', to='stock.Location', verbose_name='目标库位')),
                ('partner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.Partner', verbose_name='业务伙伴')),
                ('purchase_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='in_out_order', to='purchase.PurchaseOrder', verbose_name='采购单')),
                ('sales_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='in_out_order', to='sales.SalesOrder', verbose_name='销售单')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.Warehouse', verbose_name='仓库')),
            ],
            options={
                'verbose_name': '出入库操作',
            },
        ),
        migrations.CreateModel(
            name='InOutOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('piece', models.IntegerField(default=1, verbose_name='件')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='数量')),
                ('uom', models.CharField(choices=[('t', '吨'), ('m3', '立方'), ('m2', '平方')], default='t', max_length=10, verbose_name='计量单位')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='inoutorderitem_location', to='stock.Location', verbose_name='库位')),
                ('location_dest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='inoutorderitem_location_dest', to='stock.Location', verbose_name='目标库位')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='mrp.InOutOrder', verbose_name='对应订单')),
                ('package_list', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.PackageList', verbose_name='码单')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product', verbose_name='product')),
            ],
            options={
                'verbose_name': '出入库操作明细行',
            },
        ),
        migrations.AddField(
            model_name='expenses',
            name='expense',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mrp.ExpensesItem', verbose_name='费用名称'),
        ),
    ]
