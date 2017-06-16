from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


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
        'bookmarklet_url': bookmarklet_url
    })
