# Generated by Django 2.1.2 on 2018-12-16 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0032_auto_20181212_0152'),
    ]

    operations = [
        migrations.AddField(
            model_name='draftpackagelist',
            name='thickness',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=5, verbose_name='厚度规格'),
            preserve_default=False,
        ),
    ]