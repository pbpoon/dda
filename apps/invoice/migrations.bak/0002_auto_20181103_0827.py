# Generated by Django 2.1.2 on 2018-11-03 08:27

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderInvoiceThrough',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': '订单与账单关系',
            },
        ),
        migrations.AlterModelOptions(
            name='payment',
            options={'verbose_name': '收付款记录'},
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='object_id',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='payments',
        ),
        migrations.AddField(
            model_name='invoice',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='日期'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='type',
            field=models.CharField(choices=[('-1', '支付'), ('1', '收款')], default='-1', max_length=2, verbose_name='支付/收款'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='usage',
            field=models.CharField(choices=[('货款', '货款'), ('加工费', '加工费'), ('运费', '运费'), ('装车费', '装车费'), ('佣金', '佣金')], default='货款', max_length=20, verbose_name='款项用途'),
        ),
        migrations.AlterField(
            model_name='assign',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assign_payments', to='invoice.Invoice', verbose_name='账单'),
        ),
        migrations.AddField(
            model_name='orderinvoicethrough',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_order', to='invoice.Invoice', verbose_name='账单'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='from_order',
            field=models.ManyToManyField(related_name='to_invoice', to='invoice.OrderInvoiceThrough', verbose_name='对应订单'),
        ),
    ]
