# Quick Onboarding Checklist

## Day 57: Client #2 and #3 (<1 hour each)

---

## Pre-Onboarding (5 min)

- [ ] Client signed paid proposal
- [ ] Payment received
- [ ] Client contact info collected

---

## Step 1: Create Client (5 min)

```python
from app.agency.client_service import AgencyClientService

svc = AgencyClientService()
agency = svc.get_agency("[AGENCY_ID]")  # or create new

client = svc.create_client(
    agency.id,
    name="[CLIENT_NAME]",
    persona="[PERSONA_ID]",
    genre="[GENRE]",
    audience="[AUDIENCE]",
    monthly_quota=200
)
print(f"Client ID: {client.id}")
```

---

## Step 2: Add to Dashboard (2 min)

```python
from app.analytics.revenue_dashboard import RevenueDashboard

dash = RevenueDashboard()
dash.add_client(client.id, client.name, monthly_fee=10000, videos_quota=200)
```

---

## Step 3: First Batch (10 min)

- [ ] Collect 10-20 topics
- [ ] Run batch

```python
result = svc.generate_batch(client.id, topics=topics, count=20)
print(f"Success: {result.successful}/{result.requested}")
```

---

## Step 4: Quality Check (5 min)

- [ ] Spot check 3-5 videos
- [ ] Verify hook quality
- [ ] Confirm no issues

---

## Step 5: Handoff (5 min)

- [ ] Share WhatsApp/Slack channel
- [ ] Send first weekly report
- [ ] Schedule Week 1 check-in

---

## Total Time Target: < 30 minutes

---

## Onboarding Log

| Client | Date | Time Taken | Issues |
|--------|------|------------|--------|
| Client #2 | | | |
| Client #3 | | | |
| Client #4 | | | |
| Client #5 | | | |
