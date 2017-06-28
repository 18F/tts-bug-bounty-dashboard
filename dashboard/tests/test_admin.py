import pytest
from django.contrib.admin import AdminSite

from ..admin import (
    Report, ReportAdmin, SingletonMetadata, SingletonMetadataAdmin
)


@pytest.fixture
def report_admin():
    site = AdminSite()
    return ReportAdmin(Report, site)


@pytest.fixture
def singleton_metadata_admin():
    site = AdminSite()
    return SingletonMetadataAdmin(SingletonMetadata, site)


def test_users_cannot_add_reports(report_admin):
    assert not report_admin.has_add_permission(None)


def test_users_cannot_delete_reports(report_admin):
    assert not report_admin.has_delete_permission(None)


def test_users_cannot_add_singleton_metadata(singleton_metadata_admin):
    assert not singleton_metadata_admin.has_add_permission(None)


def test_users_cannot_delete_singleton_metadata(singleton_metadata_admin):
    assert not singleton_metadata_admin.has_delete_permission(None)
