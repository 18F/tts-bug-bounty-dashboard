import pytest
from django.contrib.admin import AdminSite

from ..admin import Report, ReportAdmin


@pytest.fixture
def report_admin():
    site = AdminSite()
    return ReportAdmin(Report, site)


def test_users_cannot_add_reports(report_admin):
    assert not report_admin.has_add_permission(None)


def test_users_cannot_delete_reports(report_admin):
    assert not report_admin.has_delete_permission(None)
