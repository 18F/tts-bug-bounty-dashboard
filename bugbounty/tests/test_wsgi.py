from .. import wsgi


def test_application_is_callable():
    assert callable(wsgi.application)
