"""
Date utility functions.

Migrated from: Macro/date_impute.sas, Macro/age.sas,
               Macro/create_datetime_range.sas, Macro/time_interval.sas,
               Macro/sql_datetime.sas
Original authors: Scott Bass

Provides date imputation, age calculation, datetime range creation,
and related utilities.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Optional, Union

import pandas as pd
from dateutil.relativedelta import relativedelta


def age(
    begdate: Union[date, datetime, pd.Timestamp],
    enddate: Optional[Union[date, datetime, pd.Timestamp]] = None,
    units: str = "YEAR",
) -> int:
    """
    Calculate age in the specified units between two dates.

    Parameters
    ----------
    begdate : date, datetime, or pd.Timestamp
        Start date (usually DOB).
    enddate : date, datetime, or pd.Timestamp, optional
        End date. Defaults to today.
    units : str
        ``"YEAR"``/``"Y"``, ``"MONTH"``/``"M"``, or ``"DAY"``/``"D"``.

    Returns
    -------
    int
        Age in the specified units (floored).
    """
    if enddate is None:
        enddate = date.today()

    begdate = _to_date(begdate)
    enddate = _to_date(enddate)

    units_upper = units.upper()
    first_char = units_upper[0] if units_upper else "Y"

    if first_char == "Y":
        rd = relativedelta(enddate, begdate)
        return rd.years
    elif first_char == "M":
        rd = relativedelta(enddate, begdate)
        return rd.years * 12 + rd.months
    elif first_char == "D":
        return (enddate - begdate).days
    else:
        raise ValueError(
            f"{units!r} is not a valid unit. "
            "Valid values: Y, YEAR, M, MONTH, D, DAY."
        )


def date_impute(
    in_y: Optional[str] = None,
    in_m: Optional[str] = None,
    in_d: Optional[str] = None,
    imp_y: Optional[int] = None,
    imp_m: int = 1,
    imp_d: int = 1,
    month_fmt: str = "MM",
    in_date: Optional[Union[date, datetime]] = None,
) -> tuple[Optional[date], bool]:
    """
    Impute a partial date from year/month/day components.

    Parameters
    ----------
    in_y : str or None
        Year component (character).
    in_m : str or None
        Month component (character). Depends on ``month_fmt``.
    in_d : str or None
        Day component (character).
    imp_y : int or None
        Default year for imputation. None means no year imputation.
    imp_m : int
        Default month for imputation. Default ``1``.
    imp_d : int
        Default day for imputation. Default ``1``.
    month_fmt : str
        ``"MM"`` (numeric, e.g. ``"07"``) or ``"MON"`` (abbreviated name).
    in_date : date, optional
        If provided, only impute when this is None/NaT.

    Returns
    -------
    tuple of (date or None, bool)
        The imputed date and a flag indicating whether imputation occurred.
    """
    if in_date is not None and not pd.isna(in_date):
        return (_to_date(in_date), False)

    y = _parse_int(in_y)
    m = _parse_month(in_m, month_fmt)
    d = _parse_int(in_d)

    imputed = (y is None) or (m is None) or (d is None)

    if y is None:
        y = imp_y
    if m is None:
        m = imp_m
    if d is None:
        d = imp_d

    if y is None or m is None or d is None:
        return (None, imputed)

    try:
        return (date(y, m, d), imputed)
    except ValueError:
        return (None, imputed)


def create_datetime_range(
    start: Union[str, datetime, pd.Timestamp],
    end: Union[str, datetime, pd.Timestamp],
    interval: str = "day",
) -> pd.DatetimeIndex:
    """
    Create a range of datetime values.

    Parameters
    ----------
    start : str or datetime
        Start of range.
    end : str or datetime
        End of range.
    interval : str
        Frequency string (e.g. ``"day"``, ``"hour"``, ``"month"``).

    Returns
    -------
    pd.DatetimeIndex
    """
    freq_map = {
        "DAY": "D",
        "HOUR": "h",
        "MINUTE": "min",
        "SECOND": "s",
        "MONTH": "MS",
        "YEAR": "YS",
        "WEEK": "W",
    }
    freq = freq_map.get(interval.upper(), interval)
    return pd.date_range(start=start, end=end, freq=freq)


def time_interval(
    start: Union[datetime, pd.Timestamp],
    end: Union[datetime, pd.Timestamp],
    units: str = "DAYS",
) -> float:
    """
    Calculate the time interval between two datetimes.

    Parameters
    ----------
    start, end : datetime or Timestamp
    units : str
        ``"DAYS"``, ``"HOURS"``, ``"MINUTES"``, ``"SECONDS"``.

    Returns
    -------
    float
    """
    delta = pd.Timestamp(end) - pd.Timestamp(start)
    total_seconds = delta.total_seconds()

    units_upper = units.upper()
    if units_upper.startswith("D"):
        return total_seconds / 86400
    if units_upper.startswith("H"):
        return total_seconds / 3600
    if units_upper.startswith("M"):
        return total_seconds / 60
    return total_seconds


def sql_datetime(dt: Union[date, datetime, pd.Timestamp]) -> str:
    """
    Format a date/datetime to SQL-compatible string.

    Returns ISO-8601 format suitable for SQL WHERE clauses.

    Parameters
    ----------
    dt : date, datetime, or Timestamp

    Returns
    -------
    str
        Formatted datetime string.
    """
    dt = pd.Timestamp(dt)
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _to_date(val: Union[date, datetime, pd.Timestamp]) -> date:
    """Convert to a Python date."""
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, datetime):
        return val.date()
    return val


def _parse_int(s: Optional[str]) -> Optional[int]:
    """Parse a string to int, returning None on failure."""
    if s is None:
        return None
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        return None


_MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _parse_month(s: Optional[str], fmt: str) -> Optional[int]:
    """Parse a month string to integer."""
    if s is None:
        return None
    s = s.strip()
    if not s or s.upper() in ("UNK", "UK"):
        return None

    if fmt.upper() == "MON":
        return _MONTH_MAP.get(s.upper()[:3])
    else:
        return _parse_int(s)
