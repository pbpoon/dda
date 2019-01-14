# Generated by Django 2.1.2 on 2019-01-14 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0018_auto_20190110_0808'),
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
                'ordering': ('city', 'id'),
            },
        ),
    ]