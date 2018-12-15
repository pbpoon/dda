# Generated by Django 2.1.2 on 2018-12-10 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0006_auto_20181210_1316'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, verbose_name='id')),
                ('name', models.CharField(max_length=20, verbose_name='名称')),
                ('city', models.IntegerField(verbose_name='对应市id')),
            ],
            options={
                'verbose_name': '地区',
                'verbose_name_plural': '地区',
            },
        ),
    ]