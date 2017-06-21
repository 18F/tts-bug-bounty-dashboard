from django.test import TestCase, override_settings
from django.conf.urls import url
from django.contrib.auth.models import User
from django.http import HttpResponse

from ..urls import urlpatterns
from ..decorators import staff_login_required


@staff_login_required
def staff_only_view(request):
    return HttpResponse('ok')


urlpatterns += [
    url(r'^staff_only_view/$', staff_only_view, name='staff_only_view'),
]


@override_settings(
    ROOT_URLCONF=__name__,
    # This will make tests run faster.
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    # Ignore our custom auth backend so we can log the user in via
    # Django 1.8's login helpers.
    AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend']
)
class StaffLoginRequiredTests(TestCase):
    def login(self, is_staff=False):
        user = User.objects.create_user(username='foo', password='bar')
        if is_staff:
            user.is_staff = True
            user.save()
        assert self.client.login(username='foo', password='bar')
        return user

    def test_redirects_to_login(self):
        res = self.client.get('/staff_only_view/')
        self.assertEqual(302, res.status_code)
        self.assertTrue(res['Location'].startswith('/auth/login'))

    def test_staff_user_is_permitted(self):
        self.login(is_staff=True)
        res = self.client.get('/staff_only_view/')
        self.assertEqual(200, res.status_code)
        self.assertEqual(b'ok', res.content)

    def test_non_staff_user_is_denied(self):
        self.login(is_staff=False)
        res = self.client.get('/staff_only_view/')
        self.assertEqual(403, res.status_code)


def test_staff_login_required_works_when_no_function_is_provided():
    dec = staff_login_required()
    assert callable(dec)
