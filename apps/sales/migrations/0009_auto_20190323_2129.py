# Generated by Django 2.1.7 on 2019-03-23 13:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0008_auto_20190321_2347'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='salesleads',
            options={'ordering': ('-state', '-created'), 'verbose_name': '销售线索'},
        ),
    ]
