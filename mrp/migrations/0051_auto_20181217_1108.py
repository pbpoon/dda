# Generated by Django 2.1.2 on 2018-12-17 11:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0013_auto_20181212_0305'),
        ('mrp', '0050_auto_20181216_1312'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventoryorderitem',
            name='draft_package_list',
        ),
        migrations.RemoveField(
            model_name='inventoryorderitem',
            name='old_location',
        ),
        migrations.AddField(
            model_name='inventoryorderitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_virtual': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='inventoryorderitem_location', to='stock.Location', verbose_name='实际库位'),
        ),
        migrations.AlterField(
            model_name='inventoryorderitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='inventoryorderitem_old_location', to='stock.Location', verbose_name='原库位'),
        ),
    ]