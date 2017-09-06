import datetime
import pytz
from businesstime import BusinessTime
from businesstime.holidays.usa import USFederalHolidays


# Number of business days we have to fix a security vulnerability.
SLA_DAYS = 90

# Days before SLA_DAYS we'll nag someone to attend to the vulnerability.
NAG_DAYS = [45, 22, 11, 5, 3, 2, 1]

# The timezone we base all "business day aware" date calculations on.
BUSINESS_TIMEZONE = 'US/Eastern'

_businesstime = BusinessTime(holidays=USFederalHolidays())


def businesstimedelta(a, b):
    '''
    Calculate the timedelta between two timezone-aware datetimes.

    Note that due to the fact that the businesstime package doesn't currently
    accept timezone-aware datetimes, we need to convert them to
    timezone-naive ones first.

    For future reference, this issue has been filed at:

        https://github.com/seatgeek/businesstime/issues/18
    '''

    # https://stackoverflow.com/a/5452709
    est = pytz.timezone(BUSINESS_TIMEZONE)
    return _businesstime.businesstimedelta(
        a.astimezone(est).replace(tzinfo=None),
        b.astimezone(est).replace(tzinfo=None),
    )


def calculate_next_nag(created_at, last_nagged_at=None):
    '''
    Given the date/time a report was issued and the date/time we
    last nagged someone to attend to it (if any), calculate the date/time of
    the next nag.
    '''

    # Partly due to apparent limitations in the businesstime package,
    # this code is horrible.

    last_nag_day = 0
    if last_nagged_at is not None:
        last_nag_day = businesstimedelta(created_at, last_nagged_at).days

    nag_days_left = [
        SLA_DAYS - days for days in NAG_DAYS
        if SLA_DAYS - days > last_nag_day
    ]

    if nag_days_left:
        next_nag_day = nag_days_left[0]
    else:
        next_nag_day = last_nag_day + 1

    dt = created_at
    while True:
        dt += datetime.timedelta(hours=24)
        days_since_creation = businesstimedelta(created_at, dt).days
        if days_since_creation >= next_nag_day:
            return dt


def contract_month(date, start_day=1):
    '''
    Return the "contract month" for a given date.

    Contracts run from some arbitrary day each month to month - for example,
    a "contract month" might be Jan 7 - Feb 6 - rather than calendar months.

    Returns a (first_day, last_day) - datetime.dates representing the contract month.
    '''
    first_day = datetime.date(date.year, date.month, start_day)
    if date.day < start_day:
        new_month = first_day.month - 1
        if new_month == 0:
            first_day = first_day.replace(year=first_day.year - 1, month=12)
        else:
            first_day = first_day.replace(month=new_month)

    last_day_year = first_day.year
    last_day_month = first_day.month + 1
    if last_day_month == 13:
        last_day_month = 1
        last_day_year += 1

    last_day = datetime.date(last_day_year, last_day_month, start_day) - datetime.timedelta(days=1)

    return first_day, last_day