# Generated by Django 2.1.2 on 2018-11-28 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0017_auto_20181128_1447'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='draftpackagelist',
            name='product',
        ),
        migrations.AddField(
            model_name='draftpackagelist',
            name='name',
            field=models.CharField(db_index=True, default=1, max_length=20, verbose_name='编号'),
            preserve_default=False,
        ),
    ]
