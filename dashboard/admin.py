from django.contrib import admin
from django.db import models
from django import forms

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
        'triaged_at',
        'is_accurate',
        'is_false_positive',
    )

    readonly_fields = Report.H1_OWNED_FIELDS
    fields = ('is_accurate', 'is_false_positive') + readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
