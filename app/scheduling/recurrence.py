"""
Recurrence Engine
Calculate next occurrences for recurring schedules.
"""
from typing import List, Optional
from datetime import datetime, timedelta, date
from app.scheduling.models import RecurrenceRule, Frequency


def calculate_next_occurrence(
    rule: RecurrenceRule,
    after: datetime = None
) -> Optional[datetime]:
    """Calculate next occurrence after given time"""
    if after is None:
        after = datetime.utcnow()
    
    # Parse time of day
    hour, minute = map(int, rule.time_of_day.split(':'))
    
    # Start from the next possible time
    candidate = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= after:
        candidate += timedelta(days=1)
    
    # Check start date
    if rule.start_date and candidate.date() < rule.start_date:
        candidate = datetime.combine(rule.start_date, candidate.time())
    
    # Check end date
    if rule.end_date and candidate.date() > rule.end_date:
        return None
    
    # Apply frequency
    if rule.frequency == Frequency.DAILY:
        candidate = _next_daily(candidate, rule, after)
    elif rule.frequency == Frequency.WEEKLY:
        candidate = _next_weekly(candidate, rule, after)
    elif rule.frequency == Frequency.MONTHLY:
        candidate = _next_monthly(candidate, rule, after)
    elif rule.frequency == Frequency.HOURLY:
        candidate = _next_hourly(after, rule)
    
    # Check exceptions
    while candidate and candidate.date() in rule.exceptions:
        candidate = calculate_next_occurrence(rule, candidate)
    
    # Check end date again
    if candidate and rule.end_date and candidate.date() > rule.end_date:
        return None
    
    return candidate


def _next_daily(candidate: datetime, rule: RecurrenceRule, after: datetime) -> datetime:
    """Calculate next daily occurrence"""
    if rule.interval > 1:
        # Every N days
        if rule.start_date:
            days_since_start = (candidate.date() - rule.start_date).days
            remainder = days_since_start % rule.interval
            if remainder != 0:
                candidate += timedelta(days=rule.interval - remainder)
    return candidate


def _next_weekly(candidate: datetime, rule: RecurrenceRule, after: datetime) -> datetime:
    """Calculate next weekly occurrence"""
    if not rule.days_of_week:
        rule.days_of_week = [1]  # Default Monday
    
    # Find next allowed day
    current_day = candidate.isoweekday()
    
    for _ in range(14):  # Search up to 2 weeks
        if current_day in rule.days_of_week:
            if candidate > after:
                return candidate
        
        candidate += timedelta(days=1)
        current_day = candidate.isoweekday()
    
    return candidate


def _next_monthly(candidate: datetime, rule: RecurrenceRule, after: datetime) -> datetime:
    """Calculate next monthly occurrence"""
    if not rule.days_of_month:
        rule.days_of_month = [1]  # Default 1st
    
    # Find next allowed day of month
    for _ in range(62):  # Search up to 2 months
        if candidate.day in rule.days_of_month:
            if candidate > after:
                return candidate
        
        candidate += timedelta(days=1)
    
    return candidate


def _next_hourly(after: datetime, rule: RecurrenceRule) -> datetime:
    """Calculate next hourly occurrence"""
    candidate = after.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    if rule.interval > 1:
        # Every N hours
        hour = candidate.hour
        remainder = hour % rule.interval
        if remainder != 0:
            candidate += timedelta(hours=rule.interval - remainder)
    
    return candidate


def get_next_n_occurrences(
    rule: RecurrenceRule,
    n: int = 10,
    after: datetime = None
) -> List[datetime]:
    """Get next N occurrences"""
    if after is None:
        after = datetime.utcnow()
    
    occurrences = []
    current = after
    
    for _ in range(n):
        next_occ = calculate_next_occurrence(rule, current)
        if next_occ is None:
            break
        occurrences.append(next_occ)
        current = next_occ
    
    return occurrences


def validate_recurrence_rule(rule: RecurrenceRule) -> List[str]:
    """Validate recurrence rule"""
    issues = []
    
    if rule.interval < 1:
        issues.append("Interval must be positive")
    
    if rule.days_of_week:
        for day in rule.days_of_week:
            if day < 1 or day > 7:
                issues.append(f"Invalid day of week: {day}")
    
    if rule.days_of_month:
        for day in rule.days_of_month:
            if day < 1 or day > 31:
                issues.append(f"Invalid day of month: {day}")
    
    if rule.start_date and rule.end_date:
        if rule.start_date > rule.end_date:
            issues.append("Start date must be before end date")
    
    if rule.count is not None and rule.count < 1:
        issues.append("Count must be positive")
    
    # Validate time format
    try:
        hour, minute = map(int, rule.time_of_day.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            issues.append("Invalid time of day")
    except ValueError:
        issues.append("Invalid time format (use HH:MM)")
    
    return issues


def create_rule_from_pattern(pattern_name: str) -> Optional[RecurrenceRule]:
    """Create recurrence rule from preset pattern"""
    from app.scheduling.models import SCHEDULE_PATTERNS
    return SCHEDULE_PATTERNS.get(pattern_name)
