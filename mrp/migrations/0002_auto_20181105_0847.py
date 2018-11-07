# Generated by Django 2.1.2 on 2018-11-05 08:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('mrp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blockcheckinorder',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='blockcheckinorder',
            name='counter',
            field=models.IntegerField(blank=True, null=True, verbose_name='货柜数'),
        ),
        migrations.AddField(
            model_name='blockcheckinorder',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='blockcheckinorderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mrp.BlockCheckInOrder', verbose_name='items'),
        ),
    ]
