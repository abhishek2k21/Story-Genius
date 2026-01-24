# Failure & Risk Review

## Day 55: Remove Single-Point Failures

---

## Instructions

Identify and mitigate risks that could break paid delivery.

---

## Tech Bottlenecks

| Bottleneck | Severity | Mitigation |
|------------|----------|------------|
| LLM API down | HIGH | Add fallback model |
| TTS service fails | HIGH | Retry + alert |
| Database crash | CRITICAL | Backup strategy |
| Rate limit hit | MEDIUM | Queue management |
| Cost spike | MEDIUM | Usage alerts |

---

## Human Bottlenecks

| Bottleneck | Severity | Mitigation |
|------------|----------|------------|
| Founder unavailable | HIGH | Document processes |
| Support overload | MEDIUM | FAQ + auto-responses |
| Onboarding manual | MEDIUM | Self-serve docs |
| Quality review | LOW | Automated scoring |

---

## Cost Spikes

| Trigger | Detection | Action |
|---------|-----------|--------|
| Runaway retries | >10 retries/job | Auto-stop |
| Long videos | >60 sec generation | Warn + limit |
| Batch overrun | >quota + 20% | Pause + alert |
| API cost spike | >₹100/day | Daily report |

---

## Trust Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low quality batch | Client complaint | Pre-delivery QA |
| Missed deadline | Churn | SLA + buffer |
| Data leak | Legal | Access controls |
| Wrong brand content | Trust loss | Lock personas |

---

## Top 3 Mitigations (Immediate)

### 1. [FILL: Highest Risk]
- **Risk**: 
- **Mitigation**: 
- **Owner**: 
- **Deadline**: 

### 2. [FILL: Second Risk]
- **Risk**: 
- **Mitigation**: 
- **Owner**: 
- **Deadline**: 

### 3. [FILL: Third Risk]
- **Risk**: 
- **Mitigation**: 
- **Owner**: 
- **Deadline**: 

---

## Emergency Playbook

| Scenario | Step 1 | Step 2 | Step 3 |
|----------|--------|--------|--------|
| System down | Kill switch | Notify clients | Fix + post-mortem |
| Quality crisis | Pause delivery | Manual review | Client call |
| Cost explosion | Disable generation | Analyze | Cap limits |

---

## Review Schedule

- [ ] Weekly: Check dashboard for risk signals
- [ ] Monthly: Full risk review
- [ ] Per client: Churn risk check
