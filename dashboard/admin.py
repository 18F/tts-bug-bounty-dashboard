from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
        'state',
        'is_accurate',
        'is_false_negative',
    )

    readonly_fields = Report.H1_OWNED_FIELDS + (
        'days_until_triage',
        'last_nagged_at',
        'next_nag_at',
    )
    fields = ('is_accurate', 'is_false_negative') + readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
