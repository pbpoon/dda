# Generated by Django 2.1.2 on 2018-12-15 10:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comment', '0006_comment_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='text',
        ),
    ]
