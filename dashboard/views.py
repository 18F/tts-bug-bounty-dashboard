from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .models import Report


def percentage(n, d):
    return int((float(n) / float(d)) * 100.0)


def get_stats():
    reports = Report.objects.all()
    count = reports.count()
    accurates = reports.filter(is_accurate=True).count()
    false_negatives = reports.filter(is_false_negative=True).count()

    return {
        'triage_accuracy': percentage(accurates, count),
        'false_negatives': percentage(false_negatives, count),
    }


def index(request):
    scheme = 'http' if settings.DEBUG else 'https'
    host = request.META['HTTP_HOST']
    bookmarklet_url = mark_safe('javascript:' + render_to_string(
        'bookmarklet.js',
        {
            'base_url': f'{scheme}://{host}'
        },
        request=request
    ).replace('\n', '').replace('"', '&quot;'))

    return render(request, 'index.html', {
        'stats': get_stats(),
        'bookmarklet_url': bookmarklet_url
    })
