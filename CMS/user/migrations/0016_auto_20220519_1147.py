# Generated by Django 3.2.2 on 2022-05-19 11:47

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0015_auto_20220515_1100'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('college', models.CharField(max_length=256)),
                ('major', models.CharField(max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='grade',
            field=models.CharField(default='', max_length=128),
        ),
    ]