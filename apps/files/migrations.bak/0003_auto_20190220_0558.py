# Generated by Django 2.1.2 on 2019-02-20 05:58

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_files_entry'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='files',
            options={'ordering': ['-created'], 'verbose_name': '文件'},
        ),
        migrations.AddField(
            model_name='files',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
    ]
