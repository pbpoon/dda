# Generated by Django 2.1.2 on 2018-12-14 04:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('invoice', '0006_auto_20181214_0330'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderinvoicethrough',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='orderinvoicethrough',
            name='invoice',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='from_order',
        ),
        migrations.AddField(
            model_name='invoice',
            name='content_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='object_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='OrderInvoiceThrough',
        ),
    ]
