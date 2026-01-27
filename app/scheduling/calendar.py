"""
Calendar View
Generate calendar data for schedules.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict

from app.scheduling.models import ScheduledJob, ScheduleStatus
from app.scheduling.recurrence import get_next_n_occurrences


def get_calendar_view(
    schedules: List[ScheduledJob],
    start_date: date,
    end_date: date,
    include_completed: bool = False,
    include_cancelled: bool = False
) -> Dict:
    """Generate calendar view data"""
    # Filter schedules
    filtered = []
    for s in schedules:
        if s.status == ScheduleStatus.COMPLETED and not include_completed:
            continue
        if s.status == ScheduleStatus.CANCELLED and not include_cancelled:
            continue
        filtered.append(s)
    
    # Group executions by date
    days = defaultdict(list)
    
    for schedule in filtered:
        if schedule.recurrence_rule:
            # Get occurrences in range
            current = datetime.combine(start_date, datetime.min.time())
            while current.date() <= end_date:
                occurrences = get_next_n_occurrences(
                    schedule.recurrence_rule,
                    n=50,
                    after=current
                )
                for occ in occurrences:
                    if start_date <= occ.date() <= end_date:
                        days[occ.date()].append({
                            "schedule_id": schedule.schedule_id,
                            "name": schedule.name,
                            "job_type": schedule.job_type.value,
                            "priority": schedule.priority.value,
                            "time": occ.strftime("%H:%M")
                        })
                break
        elif schedule.scheduled_at:
            if start_date <= schedule.scheduled_at.date() <= end_date:
                days[schedule.scheduled_at.date()].append({
                    "schedule_id": schedule.schedule_id,
                    "name": schedule.name,
                    "job_type": schedule.job_type.value,
                    "priority": schedule.priority.value,
                    "time": schedule.scheduled_at.strftime("%H:%M")
                })
    
    # Format result
    result_days = []
    current = start_date
    while current <= end_date:
        day_data = {
            "date": current.isoformat(),
            "executions": days.get(current, []),
            "count": len(days.get(current, []))
        }
        result_days.append(day_data)
        current += timedelta(days=1)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": result_days,
        "total_executions": sum(len(d) for d in days.values())
    }


def get_upcoming_executions(
    schedules: List[ScheduledJob],
    limit: int = 10,
    hours_ahead: int = 24
) -> List[Dict]:
    """Get upcoming scheduled executions"""
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours_ahead)
    
    upcoming = []
    
    for schedule in schedules:
        if schedule.status != ScheduleStatus.ACTIVE:
            continue
        
        if schedule.next_run_at and now <= schedule.next_run_at <= cutoff:
            upcoming.append({
                "schedule_id": schedule.schedule_id,
                "name": schedule.name,
                "job_type": schedule.job_type.value,
                "priority": schedule.priority.value,
                "next_run_at": schedule.next_run_at.isoformat(),
                "time_until": str(schedule.next_run_at - now)
            })
    
    # Sort by next run time
    upcoming.sort(key=lambda x: x["next_run_at"])
    
    return upcoming[:limit]


def get_week_summary(
    schedules: List[ScheduledJob],
    week_start: date
) -> Dict:
    """Get summary for a week"""
    week_end = week_start + timedelta(days=6)
    
    calendar = get_calendar_view(schedules, week_start, week_end)
    
    by_day = {}
    for day in calendar["days"]:
        day_name = datetime.fromisoformat(day["date"]).strftime("%A")
        by_day[day_name] = day["count"]
    
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_executions": calendar["total_executions"],
        "by_day": by_day
    }


def get_month_summary(
    schedules: List[ScheduledJob],
    year: int,
    month: int
) -> Dict:
    """Get summary for a month"""
    start_date = date(year, month, 1)
    
    # Calculate end of month
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    calendar = get_calendar_view(schedules, start_date, end_date)
    
    by_week = defaultdict(int)
    for day in calendar["days"]:
        day_date = date.fromisoformat(day["date"])
        week_num = day_date.isocalendar()[1]
        by_week[f"Week {week_num}"] += day["count"]
    
    return {
        "year": year,
        "month": month,
        "total_executions": calendar["total_executions"],
        "by_week": dict(by_week),
        "busiest_day": max(calendar["days"], key=lambda d: d["count"])["date"] if calendar["days"] else None
    }
