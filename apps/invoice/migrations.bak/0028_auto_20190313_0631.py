# Generated by Django 2.1.2 on 2019-03-13 06:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0027_auto_20190313_0252'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'ordering': ('-created',), 'verbose_name': '账单'},
        ),
    ]