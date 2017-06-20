from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .models import Report


def percentage(n, d):
    return int((float(n) / float(d)) * 100.0)


def get_stats():
    reports = Report.objects.all()
    count = reports.count()
    accurates = reports.filter(is_accurate=True).count()
    false_negatives = reports.filter(is_false_negative=True).count()
    triaged = reports.filter(days_until_triage__gte=0).count()
    triaged_within_one_day = reports.filter(days_until_triage__lte=1).count()

    return {
        'triage_accuracy': percentage(accurates, count),
        'false_negatives': percentage(false_negatives, count),
        'triaged_within_one_day': percentage(triaged_within_one_day, triaged)
    }


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
    return render(request, 'index.html', {
        'stats': get_stats(),
        'bookmarklet_url': get_bookmarklet_url(request)
    })


def logout_user(request):
    logout(request)
    return render(request, 'logged_out.html')
