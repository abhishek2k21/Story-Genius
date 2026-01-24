# Pilot Onboarding Script

## Day 36: First Agency Onboarding

---

## Pre-Call Checklist

- [ ] System running and tested
- [ ] Agency account created
- [ ] Kill switch ready
- [ ] Rate limits configured

---

## Onboarding Flow (30 min call)

### Step 1: Welcome (2 min)

"Thanks for being our first pilot partner. Today we'll:
1. Set up your first client
2. Generate a batch of 20 Shorts
3. Review the output together"

### Step 2: Create Agency Account (3 min)

```python
from app.agency.client_service import AgencyClientService

svc = AgencyClientService()
agency = svc.create_agency("[AGENCY_NAME]", "[AGENCY_EMAIL]")
print(f"Agency ID: {agency.id}")
```

### Step 3: Create First Client (5 min)

```python
client = svc.create_client(
    agency.id,
    name="[CLIENT_BRAND_NAME]",
    persona="fast_explainer",  # or discuss options
    visual_style="minimal_facts",
    genre="facts",  # or their genre
    audience="genz_us",  # or their audience
    monthly_quota=200
)
print(f"Client ID: {client.id}")
```

### Step 4: Generate First Batch (15 min)

```python
# Discuss topics with agency
topics = [
    "Topic 1 from agency",
    "Topic 2 from agency",
    # ... 20 topics
]

result = svc.generate_batch(client.id, topics=topics, count=20)
print(f"Generated {result.successful}/{result.requested} Shorts")
print(f"Avg Score: {result.avg_score:.2f}")
```

### Step 5: Review Output Together (5 min)

- Open generated scenes in database
- Show hook selections
- Show quality scores
- Ask for immediate reactions

---

## Post-Onboarding

- [ ] Share WhatsApp/Slack for questions
- [ ] Schedule Day 38 feedback call
- [ ] Send observation log link

---

## What to Watch For

| Signal | What it means |
|--------|---------------|
| "This is fast" | Speed value landing |
| "Can I change X?" | Control friction |
| "My team can use this" | PMF signal |
| "Let me check with client" | Decision blocker |

---

## Emergency Commands

```python
# Kill all running jobs
from app.agency.pilot_controls import get_pilot_controls
controls = get_pilot_controls()
controls.kill_switch.kill_all()

# Resume
controls.kill_switch.resume()
```
