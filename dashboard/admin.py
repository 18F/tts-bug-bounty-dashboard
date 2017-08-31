from django.contrib import admin
from .models import Report, SingletonMetadata


class TriagedWithinSLAFilter(admin.SimpleListFilter):
    title = "triage SLA"
    parameter_name = 'met_triage_sla'

    def lookups(self, request, model_admin):
        return (
            ('yes', "within triage SLA"),
            ('no', "outside triage SLA")
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(days_until_triage__lte=1)
        elif self.value() == "no":
            return queryset.filter(days_until_triage__gt=1)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
        'state',
        'is_accurate',
        'is_false_negative',
        'is_eligible_for_bounty',
        'days_until_triage',
    )

    readonly_fields = Report.H1_OWNED_FIELDS + (
        'days_until_triage',
        'last_nagged_at',
        'next_nag_at',
    )
    fields = ('is_accurate', 'is_false_negative') + readonly_fields

    list_filter = (
        TriagedWithinSLAFilter,
        'created_at',
        'is_accurate',
        'is_false_negative',
        'is_eligible_for_bounty',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SingletonMetadata)
class SingletonMetadataAdmin(admin.ModelAdmin):
    fields = ('last_synced_at',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
