# Generated by Django 2.1.2 on 2018-12-14 07:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('comment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperationLogs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('pre_data', django.contrib.postgres.fields.jsonb.JSONField(verbose_name='前数据')),
                ('change_data', django.contrib.postgres.fields.jsonb.JSONField(verbose_name='修改数据')),
                ('type', models.CharField(default='ktv', max_length=64, verbose_name='类型')),
                ('content', models.TextField(null=True, verbose_name='修改详情')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': '操作日志',
            },
        ),
    ]