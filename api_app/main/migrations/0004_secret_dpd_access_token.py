# Generated by Django 5.0.3 on 2024-04-23 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_secret_refresh_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='secret',
            name='dpd_access_token',
            field=models.CharField(max_length=999, null=True),
        ),
    ]