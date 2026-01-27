"""
Timezone Utilities
Handle timezone conversions for scheduling.
"""
from datetime import datetime, timezone
from typing import Optional
import re


# Common timezones
SUPPORTED_TIMEZONES = {
    "UTC": 0,
    "America/New_York": -5,
    "America/Los_Angeles": -8,
    "America/Chicago": -6,
    "America/Denver": -7,
    "Europe/London": 0,
    "Europe/Paris": 1,
    "Europe/Berlin": 1,
    "Asia/Tokyo": 9,
    "Asia/Shanghai": 8,
    "Asia/Kolkata": 5.5,
    "Asia/Dubai": 4,
    "Australia/Sydney": 11,
    "Pacific/Auckland": 13
}


def to_utc(dt: datetime, tz_name: str) -> datetime:
    """Convert local time to UTC"""
    if tz_name == "UTC":
        return dt
    
    offset_hours = SUPPORTED_TIMEZONES.get(tz_name, 0)
    return dt - timedelta(hours=offset_hours)


def from_utc(dt: datetime, tz_name: str) -> datetime:
    """Convert UTC to local time"""
    if tz_name == "UTC":
        return dt
    
    offset_hours = SUPPORTED_TIMEZONES.get(tz_name, 0)
    return dt + timedelta(hours=offset_hours)


def get_offset_string(tz_name: str) -> str:
    """Get UTC offset string"""
    offset = SUPPORTED_TIMEZONES.get(tz_name, 0)
    sign = "+" if offset >= 0 else "-"
    hours = abs(int(offset))
    minutes = int((abs(offset) % 1) * 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def list_timezones() -> list:
    """List all supported timezones"""
    return [
        {"name": name, "offset": get_offset_string(name)}
        for name in SUPPORTED_TIMEZONES
    ]


def is_valid_timezone(tz_name: str) -> bool:
    """Check if timezone is supported"""
    return tz_name in SUPPORTED_TIMEZONES


def now_in_timezone(tz_name: str) -> datetime:
    """Get current time in specified timezone"""
    utc_now = datetime.utcnow()
    return from_utc(utc_now, tz_name)


# Import timedelta here to avoid circular issues
from datetime import timedelta
