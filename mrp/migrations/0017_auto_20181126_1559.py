# Generated by Django 2.1.2 on 2018-11-26 15:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mrp', '0016_auto_20181126_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movelocationorderitem',
            name='location',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_virtual': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='movelocationorderitem_location', to='stock.Location', verbose_name='库位'),
        ),
        migrations.AlterField(
            model_name='movelocationorderitem',
            name='location_dest',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_virtual': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='movelocationorderitem_location_dest', to='stock.Location', verbose_name='目标库位'),
        ),
    ]
