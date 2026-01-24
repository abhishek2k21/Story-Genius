# Pilot Execution Checklist

## Day 43-46: Running Live Pilots

---

## Pre-Pilot Setup

- [ ] System running and stable
- [ ] Kill switch tested
- [ ] Rate limits configured
- [ ] Agency account created
- [ ] Client profile set up

---

## Pilot #1 Execution

### Agency: [AGENCY_NAME]
### Date: [DATE]
### Shorts Target: 20-30

---

### Step 1: Kickoff (5 min)

```python
from app.agency.client_service import AgencyClientService

svc = AgencyClientService()
# Use existing agency or create new
client = svc.get_client("[CLIENT_ID]")
```

### Step 2: Collect Topics

Topics from agency:
1.
2.
3.
... (20-30 topics)

### Step 3: Generate Batch

```python
result = svc.generate_batch(
    client.id,
    topics=topics,
    count=20
)
print(f"Success: {result.successful}/{result.requested}")
print(f"Avg Score: {result.avg_score:.2f}")
```

### Step 4: Record Results

| Metric | Value |
|--------|-------|
| Videos Requested | |
| Videos Successful | |
| Success Rate | |
| Avg Quality Score | |
| Total Time (sec) | |
| Blocking Issues | |

---

## Observation Triggers

Watch for and log:

- [ ] "How do I...?" → UX friction
- [ ] Long pause → Confusion
- [ ] "Can I change...?" → Control friction
- [ ] "This is slow" → Performance issue
- [ ] "Wow" / "Nice" → Magic moment
- [ ] Skipping feature → Not valued

---

## Post-Pilot Immediate Notes

What worked:
>

What didn't:
>

Biggest surprise:
>

---

## Pilot #2 (Day 46)

### Agency: [AGENCY_NAME_2]
### Differences from Pilot #1:

| Aspect | Pilot #1 | Pilot #2 |
|--------|----------|----------|
| Hand-holding | | |
| Questions asked | | |
| Pain points | | |
| Magic moments | | |

### ICP Adjustment Needed?
- [ ] No, consistent signals
- [ ] Yes, need to adjust [WHAT]
