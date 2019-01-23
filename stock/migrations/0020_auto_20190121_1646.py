# Generated by Django 2.1.2 on 2019-01-21 16:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0019_auto_20190116_0501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='warehouse',
            name='partner',
            field=models.ForeignKey(blank=True, limit_choices_to={'type__in': ('production', 'supplier')}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='warehouse', to='partner.Partner', verbose_name='合作伙伴'),
        ),
    ]
