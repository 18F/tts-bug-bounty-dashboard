"""bugbounty URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from .decorators import staff_login_required
import dashboard.views


# Wrap the admin site login with our staff_login_required decorator,
# which will raise a PermissionDenied exception if a logged-in, but non-staff
# user attempts to access the login page.
# ref: http://stackoverflow.com/a/38520951
admin.site.login = staff_login_required(admin.site.login)

urlpatterns = [
    url(r'^$', dashboard.views.index, name='index'),
    url(r'^logout/$', dashboard.views.logout_user, name='logout'),
    url(r'^auth/', include('uaa_client.urls')),
    url(r'^admin/', admin.site.urls),
]
