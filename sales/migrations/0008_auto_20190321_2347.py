# Generated by Django 2.1.7 on 2019-03-21 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0007_auto_20190321_2327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesleads',
            name='category',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='product.Category', verbose_name='品种名称'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='salesleads',
            name='state',
            field=models.CharField(choices=[('0%', '错失'), ('10%', '新线索'), ('30%', '取得确认'), ('70%', '报价阶段'), ('90%', '成功在望'), ('100%', '赢得')], default='10%', max_length=20, verbose_name='状态'),
        ),
    ]
