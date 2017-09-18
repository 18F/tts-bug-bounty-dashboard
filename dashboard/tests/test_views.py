import pytest
from django.contrib.auth.models import User
from django.utils.safestring import SafeString

from .. import views


@pytest.fixture
def some_user(db):
    user = User(username='foo', email='foo@gsa.gov')
    user.save()
    return user


@pytest.fixture
def some_user_client(some_user, client):
    client.force_login(some_user)
    return client


def test_get_bookmarklet_url_works(rf):
    request = rf.get('/')
    request.META['HTTP_HOST'] = 'boop.gov'
    url = views.get_bookmarklet_url(request)
    assert url.startswith('javascript:')
    assert '"' not in url
    assert 'https://boop.gov' in url
    assert isinstance(url, SafeString)


def test_logout_works(some_user_client):
    response = some_user_client.get('/logout/')
    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated()


def test_index_returns_200(some_user_client):
    response = some_user_client.get('/', **{'HTTP_HOST': 'boop.gov'})
    assert response.status_code == 200


def test_index_requires_logged_in_user(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response['location'] == '/auth/login?next=/'

def test_bounty_list(some_user_client):
    response = some_user_client.get('/bounties/')
    assert response.status_code == 200
