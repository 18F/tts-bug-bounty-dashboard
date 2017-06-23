import pytz
from datetime import datetime

from ..dates import calculate_next_nag, businesstimedelta


def test_calculate_next_nag_works_when_never_nagged():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    next_nag_at = calculate_next_nag(created_at)
    assert businesstimedelta(created_at, next_nag_at).days == 45


def test_calculate_next_nag_works_when_nagged_once():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    last_nagged_at = calculate_next_nag(created_at)
    next_nag_at = calculate_next_nag(created_at, last_nagged_at)
    assert businesstimedelta(created_at, next_nag_at).days == 68


def test_calculate_next_nag_works_when_nagged_a_ton():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    last_nagged_at = None
    nag_days = []
    for _ in range(10):
        last_nagged_at = calculate_next_nag(created_at, last_nagged_at)
        nag_days.append(businesstimedelta(created_at, last_nagged_at).days)
    assert nag_days == [45, 68, 79, 85, 87, 88, 89, 90, 91, 92]
