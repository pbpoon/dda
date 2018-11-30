# Generated by Django 2.1.2 on 2018-11-25 05:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0010_auto_20181125_0544'),
        ('mrp', '0010_auto_20181109_0933'),
    ]

    operations = [
        migrations.AddField(
            model_name='blockcheckinorderitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='blockcheckinorderitem_location', to='stock.Location', verbose_name='库位'),
        ),
        migrations.AddField(
            model_name='blockcheckinorderitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='blockcheckinorderitem_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AddField(
            model_name='kesorder',
            name='warehouse',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='stock.Warehouse', verbose_name='仓库'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kesorderproduceitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='kesorderproduceitem_location', to='stock.Location', verbose_name='库位'),
        ),
        migrations.AddField(
            model_name='kesorderproduceitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='kesorderproduceitem_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AddField(
            model_name='kesorderrawitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='kesorderrawitem_location', to='stock.Location', verbose_name='库位'),
        ),
        migrations.AddField(
            model_name='kesorderrawitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='kesorderrawitem_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AlterField(
            model_name='blockcheckinorder',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blockcheckinorder_location', to='stock.Location', verbose_name='原库位'),
        ),
        migrations.AlterField(
            model_name='blockcheckinorder',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blockcheckinorder_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AlterField(
            model_name='kesorder',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kesorder_location', to='stock.Location', verbose_name='原库位'),
        ),
        migrations.AlterField(
            model_name='kesorder',
            name='location_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kesorder_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
        migrations.AlterField(
            model_name='kesorderrawitem',
            name='price',
            field=models.DecimalField(decimal_places=2, help_text='立方单价', max_digits=8, verbose_name='单价'),
        ),
    ]
