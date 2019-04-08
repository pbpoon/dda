# Generated by Django 2.1.7 on 2019-03-13 16:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sales', '0001_initial'),
        ('partner', '0001_initial'),
        ('stock', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0002_auto_20190313_1615'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesorderitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='salesorderitem_location', to='stock.Location', verbose_name='库位'),
        ),
        migrations.AddField(
            model_name='salesorderitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='salesorderitem_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AddField(
            model_name='salesorderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='sales.SalesOrder', verbose_name='销售订单'),
        ),
        migrations.AddField(
            model_name='salesorderitem',
            name='package_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.PackageList', verbose_name='码单'),
        ),
        migrations.AddField(
            model_name='salesorderitem',
            name='product',
            field=models.ForeignKey(limit_choices_to={'type__in': ('block', 'slab')}, on_delete=django.db.models.deletion.CASCADE, related_name='sales_order_item', to='product.Product', verbose_name='产品'),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.City', verbose_name='城市'),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salesorder_entry', to=settings.AUTH_USER_MODEL, verbose_name='登记人'),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='handler',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salesorder_handler', to=settings.AUTH_USER_MODEL, verbose_name='经办人'),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_order', to='partner.Customer', verbose_name='客户名称'),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='province',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.Province', verbose_name='省份'),
        ),
    ]