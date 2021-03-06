# Generated by Django 2.1.2 on 2019-01-02 15:29

from django.db import migrations, models
import django.db.models.deletion
import files.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('content', models.FileField(upload_to=files.models.get_upload_to)),
                ('desc', models.CharField(blank=True, max_length=120, null=True, verbose_name='简述')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': '文件',
            },
        ),
    ]
