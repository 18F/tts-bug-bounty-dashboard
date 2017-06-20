from django.contrib.auth import REDIRECT_FIELD_NAME, decorators
from django.core.exceptions import PermissionDenied


def staff_login_required(function=None,
                         redirect_field_name=REDIRECT_FIELD_NAME,
                         login_url=None):
    '''
    Decorator to check that the user accessing the decorated view has their
    is_staff flag set to True.
    It will first redirect to login_url or the default login url if the user is
    not authenticated. If the user is authenticated but is not staff, then
    a PermissionDenied exception will be raised.
    '''

    # Based off code from the Django project
    # License: https://github.com/django/django/blob/c1aec0feda73ede09503192a66f973598aef901d/LICENSE  # NOQA
    # Code reference: https://github.com/django/django/blob/c1aec0feda73ede09503192a66f973598aef901d/django/contrib/auth/decorators.py#L40  # NOQA
    def check_if_staff(user):
        if not user.is_authenticated():
            # returning False will cause the user_passes_test decorator
            # to redirect to the login flow
            return False

        if user.is_staff:
            # then all good
            return True

        # otherwise the user is authenticated but isn't staff, so
        # they do not have the correct permissions and should be directed
        # to the 403 page
        raise PermissionDenied

    actual_decorator = decorators.user_passes_test(
        check_if_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
