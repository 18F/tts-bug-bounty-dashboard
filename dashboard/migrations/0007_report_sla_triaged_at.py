# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-13 20:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_bounty'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='sla_triaged_at',
            field=models.DateTimeField(blank=True, help_text='Date when we consider the issue triaged for SLA purposes, which may or may not agree with triaged_at.', null=True),
        ),
    ]