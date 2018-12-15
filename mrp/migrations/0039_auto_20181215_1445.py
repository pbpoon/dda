# Generated by Django 2.1.2 on 2018-12-15 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0038_auto_20181215_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryorder',
            name='warehouse',
            field=models.ForeignKey(blank=True, help_text='盘点的仓库', null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Warehouse', verbose_name='仓库'),
        ),
    ]
