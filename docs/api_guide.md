# Story Genius API Guide
*Creator Reality Interface*

## Base URL
`http://localhost:8000/v1`

## 1. Video Preview
Generate a lightweight preview before committing to full render.

### Generate Preview
`POST /v1/preview`
```json
{
  "topic": "The hidden history of coffee",
  "audience": "general_adult",
  "tone": "neutral",
  "scenes": 5
}
```
**Response:** Returns script, visual descriptions, estimated cost, and hook score prediction.

## 2. Script Editor
Modify the generated script to your liking.

### Edit Scene Text
`PATCH /v1/preview/{id}/scene/{idx}?text=New%20narration`
**Response:** Updated preview with recalculated duration.

## 3. Brand Kits
Manage visual styles and channel preferences.

### Create Kit
`POST /v1/branding/kits?user_id=123&name=MyChannel&style=cinematic`

### List Kits
`GET /v1/branding/kits/{user_id}`

## 4. Content Calendar
Plan batches of content.

### Create Plan
`POST /v1/calendar/plan?user_id=123&start_date=2026-02-01&end_date=2026-02-28&freq=3`
**Response:** Generated schedule with 12 video slots (3 per week).

## 5. Performance Analytics
Track what works.

### Get Top Videos
`GET /v1/analytics/top/{user_id}?metric=views`

### Get Insights
`GET /v1/analytics/insights/{user_id}`
**Response:** Aggregated stats on best retention hooks, durations, and posting times.
