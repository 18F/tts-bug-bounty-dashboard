# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-23 12:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('title', models.TextField()),
                ('created_at', models.DateTimeField()),
                ('triaged_at', models.DateTimeField(blank=True, null=True)),
                ('state', models.CharField(choices=[('new', 'new'), ('triaged', 'triaged'), ('needs-more-info', 'needs-more-info'), ('resolved', 'resolved'), ('not-applicable', 'not-applicable'), ('informative', 'informative'), ('duplicate', 'duplicate'), ('spam', 'spam')], max_length=30)),
                ('is_eligible_for_bounty', models.NullBooleanField()),
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('is_accurate', models.BooleanField(default=True, help_text="Whether we agree with HackerOne's triage assessment.")),
                ('is_false_negative', models.BooleanField(default=False, help_text='Whether HackerOne improperly classified the report as invalid or duplicate.')),
                ('days_until_triage', models.IntegerField(blank=True, help_text='Number of business days between a report being filed and being triaged.', null=True)),
                ('last_synced_at', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='SingletonMetadata',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('last_synced_at', models.DateTimeField(blank=True, help_text='When the dashboard was last synced with HackerOne.', null=True)),
            ],
        ),
    ]
