# Generated by Django 4.1.2 on 2024-12-28 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0004_agentschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='manager_photos/'),
        ),
    ]
