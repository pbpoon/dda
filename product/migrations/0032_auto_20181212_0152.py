# Generated by Django 2.1.2 on 2018-12-12 01:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0031_packagelist_from_package_list'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='block',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.Block', verbose_name='荒料编号'),
        ),
    ]