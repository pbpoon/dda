# Generated by Django 2.1.2 on 2018-11-05 15:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0003_auto_20181105_1452'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blockcheckinorderitem',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='mrp.BlockCheckInOrder'),
        ),
    ]
