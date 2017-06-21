from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .models import Report


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
        'stats': Report.get_stats(),
        'bookmarklet_url': get_bookmarklet_url(request)
    })


def logout_user(request):
    logout(request)
    return render(request, 'logged_out.html')
