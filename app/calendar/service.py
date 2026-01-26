"""
Week 18 Day 4 - Content Calendar Service
Plan 7-30 days of content in advance.
Creators think in batches, not single videos.
"""
from typing import List, Optional, Dict
from datetime import date, timedelta, time
import random

from app.calendar.models import CalendarPlan, CalendarSlot, PlanStatus, SlotStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class CalendarService:
    """Service to generate and manage content plans."""
    
    def __init__(self):
        self._plans: Dict[str, CalendarPlan] = {}
        
    def create_plan(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        frequency: int = 3,
        themes: List[str] = None,
        brand_kit_id: Optional[str] = None
    ) -> CalendarPlan:
        """
        Generate a content plan with empty slots.
        """
        if not themes:
            themes = ["Update", "Tip", "Story"]
            
        plan = CalendarPlan(
            user_id=user_id,
            name=f"Plan {start_date} to {end_date}",
            start_date=start_date,
            end_date=end_date,
            frequency_per_week=frequency,
            themes=themes,
            brand_kit_id=brand_kit_id
        )
        
        # Generate slots
        current = start_date
        while current <= end_date:
            # Simple logic: MWF if frequency is 3
            day_of_week = current.weekday() # 0=Mon, 6=Sun
            
            should_schedule = False
            if frequency == 7:
                should_schedule = True
            elif frequency == 3:
                should_schedule = day_of_week in [0, 2, 4] # Mon, Wed, Fri
            elif frequency == 1:
                should_schedule = day_of_week == 2 # Wed
            else:
                should_schedule = True # Fallback
                
            if should_schedule:
                # Assign theme
                theme = random.choice(themes)
                slot = CalendarSlot(
                    date=current,
                    time=time(18, 0), # 6 PM default
                    theme=theme
                )
                plan.slots.append(slot)
            
            current += timedelta(days=1)
            
        self._plans[plan.id] = plan
        logger.info(f"Created plan {plan.id} with {len(plan.slots)} slots")
        return plan
        
    def get_plan(self, plan_id: str) -> Optional[CalendarPlan]:
        return self._plans.get(plan_id)
        
    def update_slot_topic(self, plan_id: str, slot_id: str, topic: str):
        """Assign a specific topic to a slot."""
        plan = self.get_plan(plan_id)
        if plan:
            for slot in plan.slots:
                if slot.id == slot_id:
                    slot.topic = topic
                    slot.status = SlotStatus.PLANNED
                    return slot
        raise ValueError("Slot not found")
        
    def schedule_generation(self, plan_id: str):
        """
        Trigger generation for all planned slots.
        In real app, this would queue jobs.
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return
            
        count = 0
        for slot in plan.slots:
            if slot.status == SlotStatus.PLANNED and slot.topic:
                # Here we would call JobService to create a job
                # slot.job_id = job_service.create_job(...)
                slot.status = SlotStatus.GENERATED # Simulating instant generation
                count += 1
                
        plan.status = PlanStatus.SCHEDULED
        logger.info(f"Scheduled {count} generations for plan {plan_id}")


# Singleton
_calendar_service = None

def get_calendar_service() -> CalendarService:
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service
