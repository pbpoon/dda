# Generated by Django 2.1.2 on 2018-12-13 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0031_turnbackorder_turnbackorderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='turnbackorder',
            name='state',
            field=models.CharField(choices=[('draft', '草稿'), ('confirm', '确认'), ('done', '完成'), ('cancel', '取消')], default='draft', max_length=20, verbose_name='状态'),
        ),
    ]