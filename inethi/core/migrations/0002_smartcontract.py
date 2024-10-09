# Generated by Django 5.1 on 2024-10-08 14:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SmartContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('write_access', models.BooleanField(default=False)),
                ('read_access', models.BooleanField(default=False)),
                ('contract_type', models.CharField(choices=[('accounts index', 'Accounts Index'), ('eth faucet', 'Eth Faucet'), ('other', 'Other')], default='other', max_length=50)),
                ('user', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]