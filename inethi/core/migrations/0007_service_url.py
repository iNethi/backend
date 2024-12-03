# Generated by Django 5.1 on 2024-11-15 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_service_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='url',
            field=models.URLField(default='http://google.com', unique=True),
            preserve_default=False,
        ),
    ]
