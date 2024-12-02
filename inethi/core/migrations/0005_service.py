# Generated by Django 5.1 on 2024-11-15 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_faucetsmartcontract_owner_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('entertainment', 'Entertainment'), ('learning', 'Learning'), ('utility', 'Utility')], default='utility', max_length=50)),
                ('paid', models.BooleanField(default=False)),
            ],
        ),
    ]