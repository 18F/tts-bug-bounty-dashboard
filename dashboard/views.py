from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.humanize.templatetags.humanize import naturaltime, ordinal

from .models import Report, SingletonMetadata


def get_bookmarklet_url(request):
    scheme = 'http' if settings.DEBUG else 'https'
    host = request.META['HTTP_HOST']
    return mark_safe('javascript:' + render_to_string(
        'bookmarklet.js',
        {
            'base_url': f'{scheme}://{host}'
        },
        request=request
    ).replace('\n', '').replace('"', '&quot;'))


@login_required
def index(request):
    contract_month_start_day = getattr(settings, 'SLA_METRICS_CONTRACT_START_DAY', 1)
    stats = Report.get_stats(contract_month_start_day)

    return render(request, 'index.html', {
        'last_synced_at': naturaltime(SingletonMetadata.load().last_synced_at),
        'stats': stats,
        'totals': stats.pop('totals'),
        'bookmarklet_url': get_bookmarklet_url(request),
        'contract_month_start_day': contract_month_start_day,
        'contract_month_start_day_ordinal': ordinal(contract_month_start_day),
    })


def logout_user(request):
    logout(request)
    return render(request, 'logged_out.html')
