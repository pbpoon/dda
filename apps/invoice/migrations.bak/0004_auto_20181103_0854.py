# Generated by Django 2.1.2 on 2018-11-03 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0003_auto_20181103_0849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='partner.Partner', verbose_name='对方'),
        ),
    ]
