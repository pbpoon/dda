# Generated by Django 2.1.2 on 2019-01-03 15:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0039_auto_20190103_1533'),
        ('purchase', '0027_auto_20181230_0756'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='batch',
            field=models.CharField(blank=True, help_text='如果不填，则', max_length=10, null=True, verbose_name='批次'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='product.Category', verbose_name='品种分类'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='quarry',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='product.Quarry', verbose_name='矿口'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='batch',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='批次'),
        ),
    ]
