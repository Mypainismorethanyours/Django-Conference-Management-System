# Generated by Django 3.2.4 on 2021-06-25 15:07

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20210625_1230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.UUIDField(default=uuid.UUID('902e6753-306c-4d2e-8e20-49332e64d2a3'), primary_key=True, serialize=False),
        ),
    ]