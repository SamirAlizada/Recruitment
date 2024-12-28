# Generated by Django 4.1.2 on 2024-12-28 06:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0003_agent_icbari_1_agent_icbari_2_agent_konullu_1_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('schedule_type', models.CharField(choices=[('i', 'i/e'), ('qb', 'qb')], max_length=2)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agents.agent')),
            ],
            options={
                'unique_together': {('agent', 'date')},
            },
        ),
    ]