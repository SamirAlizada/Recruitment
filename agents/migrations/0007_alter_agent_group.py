# Generated by Django 4.1.2 on 2024-12-29 08:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0006_agent_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='agents.group'),
        ),
    ]