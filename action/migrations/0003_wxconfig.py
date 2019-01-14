# Generated by Django 2.1.2 on 2019-01-12 14:28

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action', '0002_auto_20181101_1541'),
    ]

    operations = [
        migrations.CreateModel(
            name='WxConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='应用名称')),
                ('corp_id', models.CharField(max_length=80)),
                ('values', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'verbose_name': '微信企业设置',
            },
        ),
    ]