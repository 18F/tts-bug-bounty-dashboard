from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^bounties/$', views.bounty_list, name='bounty_list'),
    url(r'^logout/$', views.logout_user, name='logout'),
]


