"""
Tests for sas_utils.data_manipulation.date_utils

Derived from Macro/age.sas, Macro/date_impute.sas Usage blocks.
"""

from datetime import date, datetime

import pandas as pd
import pytest

from sas_utils.data_manipulation.date_utils import (
    age,
    create_datetime_range,
    date_impute,
    sql_datetime,
    time_interval,
)


# ====================================================================
# Test: age calculation
# From: age.sas - age in years, months, days
# ====================================================================
class TestAge:
    def test_age_years(self):
        dob = date(1960, 12, 25)
        end = date(2005, 12, 25)
        assert age(dob, end, units="YEAR") == 45

    def test_age_months(self):
        dob = date(1960, 12, 25)
        end = date(2005, 12, 25)
        assert age(dob, end, units="MONTH") == 540

    def test_age_days(self):
        dob = date(1960, 12, 25)
        end = date(2005, 12, 25)
        assert age(dob, end, units="DAY") == (end - dob).days

    def test_age_default_today(self):
        dob = date(2000, 1, 1)
        result = age(dob)
        assert result >= 25  # We're in 2026

    def test_age_short_units(self):
        dob = date(1990, 6, 15)
        end = date(2020, 6, 15)
        assert age(dob, end, units="Y") == 30
        assert age(dob, end, units="M") == 360

    def test_age_with_timestamps(self):
        dob = pd.Timestamp("1990-01-01")
        end = pd.Timestamp("2020-01-01")
        assert age(dob, end) == 30

    def test_invalid_units(self):
        with pytest.raises(ValueError, match="not a valid unit"):
            age(date(2000, 1, 1), date(2020, 1, 1), units="INVALID")


# ====================================================================
# Test: date imputation
# From: date_impute.sas - impute partial dates
# ====================================================================
class TestDateImpute:
    def test_full_date_no_imputation(self):
        result, imputed = date_impute(
            in_y="2010", in_m="07", in_d="28",
        )
        assert result == date(2010, 7, 28)
        assert imputed is False

    def test_missing_day_imputed(self):
        result, imputed = date_impute(
            in_y="2010", in_m="07", in_d="UNK",
            imp_d=1,
        )
        assert result == date(2010, 7, 1)
        assert imputed is True

    def test_missing_month_imputed(self):
        result, imputed = date_impute(
            in_y="2010", in_m="UNK", in_d="28",
            imp_m=1,
        )
        assert result == date(2010, 1, 28)
        assert imputed is True

    def test_missing_year_no_default(self):
        result, imputed = date_impute(
            in_y="UNK", in_m="07", in_d="28",
            imp_y=None,
        )
        assert result is None
        assert imputed is True

    def test_missing_year_with_default(self):
        result, imputed = date_impute(
            in_y="UNK", in_m="07", in_d="28",
            imp_y=2026,
        )
        assert result == date(2026, 7, 28)
        assert imputed is True

    def test_all_missing(self):
        result, imputed = date_impute(
            in_y="UNK", in_m="UNK", in_d="UNK",
        )
        assert result is None
        assert imputed is True

    def test_mon_format(self):
        result, imputed = date_impute(
            in_y="2010", in_m="JUL", in_d="28",
            month_fmt="MON",
        )
        assert result == date(2010, 7, 28)
        assert imputed is False

    def test_in_date_not_missing(self):
        existing = date(2020, 1, 1)
        result, imputed = date_impute(
            in_y="2010", in_m="07", in_d="28",
            in_date=existing,
        )
        assert result == existing
        assert imputed is False


# ====================================================================
# Test: create_datetime_range
# ====================================================================
class TestCreateDatetimeRange:
    def test_daily_range(self):
        result = create_datetime_range("2020-01-01", "2020-01-10", "day")
        assert len(result) == 10

    def test_monthly_range(self):
        result = create_datetime_range("2020-01-01", "2020-06-01", "month")
        assert len(result) == 6


# ====================================================================
# Test: time_interval
# ====================================================================
class TestTimeInterval:
    def test_days(self):
        start = datetime(2020, 1, 1)
        end = datetime(2020, 1, 11)
        assert time_interval(start, end, "days") == 10.0

    def test_hours(self):
        start = datetime(2020, 1, 1, 0, 0)
        end = datetime(2020, 1, 1, 6, 0)
        assert time_interval(start, end, "hours") == 6.0


# ====================================================================
# Test: sql_datetime
# ====================================================================
class TestSqlDatetime:
    def test_date_only(self):
        result = sql_datetime(date(2020, 1, 15))
        assert result == "2020-01-15"

    def test_datetime_with_time(self):
        result = sql_datetime(datetime(2020, 1, 15, 10, 30, 45))
        assert result == "2020-01-15 10:30:45"
