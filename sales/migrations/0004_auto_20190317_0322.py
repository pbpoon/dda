# Generated by Django 2.1.7 on 2019-03-17 03:22

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_auto_20190314_0403'),
        ('sales', '0003_salesleads'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='salesleads',
            name='ps',
        ),
        migrations.AddField(
            model_name='salesleads',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.Category', verbose_name='品种名称'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='desc',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='摘要'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='due_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='截至时间'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='height_gt',
            field=models.IntegerField(blank=True, null=True, verbose_name='高(最高)'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='height_lt',
            field=models.IntegerField(blank=True, null=True, verbose_name='高(最低)'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='long_gt',
            field=models.IntegerField(blank=True, null=True, verbose_name='长(最高)'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='long_lt',
            field=models.IntegerField(blank=True, null=True, verbose_name='长(最低)'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='quantity',
            field=models.IntegerField(blank=True, null=True, verbose_name='数量'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='开始时间'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='thickness',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=2, max_digits=4), blank=True, null=True, size=None, verbose_name='厚度规格'),
        ),
        migrations.AddField(
            model_name='salesleads',
            name='type',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('block', '荒料'), ('slab', '板材')], default='slab', max_length=10), blank=True, null=True, size=None, verbose_name='类型'),
        ),
    ]
