#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manipulate dates
"""

from datetime import datetime, timedelta, timezone, date
import pytz
from time import struct_time


def dt2date(dt: datetime, tz=pytz.utc) -> date:
    """
    Convert a datetime into a date
    """
    if dt.tzinfo != tz:
        this_dt = dt.astimezone(tz=tz)
    else:
        this_dt = dt
    return date(year=this_dt.year, month=this_dt.month, day=this_dt.day)


def iso2date(iso_dt: str, tz=pytz.utc) -> date:
    """
    Convert a string containing an ISO datetime expression into a python date,
    respecting the requested timezone
    """
    dt = iso2dt(iso_dt=iso_dt, tz=tz)
    return dt2date(dt, tz=tz)


def iso2dt(iso_dt: str, tz=pytz.utc) -> datetime:
    """
    Convert a string containing an ISO datetime expression into a timzone-aware python datetime
    """
    dt = datetime.fromisoformat(iso_dt)
    if dt.tzinfo != tz:
        dt = dt.astimezone(tz=tz)
    return dt


def st2dt(st: struct_time, tz=pytz.utc) -> datetime:
    """
    Convert a time structure into a timezone-aware python datetime

    Adapted from code by Nadia Alramli with Sam Mason
    https://stackoverflow.com/questions/1697815/how-do-you-convert-a-time-struct-time-object-into-a-datetime-object#answer-1697838
    """
    if st.tm_gmtoff is not None:
        this_tz = timezone(timedelta(seconds=st.tm_gmtoff))
    else:
        # force it
        this_tz = tz
    if st.tm_sec in {60, 61}:
        dt = datetime(*st[:5], 59, tzinfo=this_tz)
    else:
        dt = datetime(*st[:6], tzinfo=this_tz)
    if dt.tzinfo != tz:
        dt = dt.astimezone(tz=tz)
    return dt
