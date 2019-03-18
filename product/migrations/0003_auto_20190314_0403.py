# Generated by Django 2.1.7 on 2019-03-14 04:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_auto_20190313_1615'),
    ]

    operations = [
        migrations.CreateModel(
            name='SlabYieldSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thickness', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='厚度规格')),
                ('min_yield', models.DecimalField(decimal_places=2, help_text='低于此值，会提示', max_digits=5, verbose_name='最低出材率')),
                ('updated', models.DateField(auto_now=True, verbose_name='更新日期')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slab_yield_set', to='product.Category', verbose_name='品种名称')),
            ],
            options={
                'verbose_name': '出材率标准值设置表',
            },
        ),
        migrations.AlterUniqueTogether(
            name='slabyieldset',
            unique_together={('category', 'thickness')},
        ),
    ]
