# Generated by Django 2.1.2 on 2018-11-30 15:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0021_auto_20181130_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionorderproduceitem',
            name='raw_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produces', to='mrp.ProductionOrderRawItem', verbose_name='原材料'),
        ),
    ]
