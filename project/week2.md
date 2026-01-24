🗓️ WEEK 2 EXECUTION PLAN
Goal: Quality Jump + Creative Intelligence
🎯 Week-2 North Star

By end of Week 2:

The same system produces visibly better Shorts because it understands hooks, personas, and emotions — not because prompts were tweaked.

This is the week where:

output quality jumps

consistency appears

you start seeing style

WEEK 2 STRUCTURE (High Level)
Theme	Outcome
Hook Intelligence	First 3 seconds become addictive
Persona System	Content feels branded
Emotion Curves	Pacing feels intentional
Critic Upgrade	Quality improves automatically
Memory (v1)	System starts learning
🟢 DAY 8 — Hook Engine (Most Important Day)
🎯 Objective

Replace “single hook” with hook exploration + selection.

What to Build
1️⃣ Hook Engine module

Create:

app/strategy/hook_engine.py


Responsibilities:

Generate 5–10 hook variants

Classify hook type

Score hooks (clarity + curiosity)

Example hook types:

Pattern interrupt

Question gap

Shock statement

Visual contradiction

2️⃣ Hook selection logic

Pick top 1 hook and discard others.

Output:

{
  "hook_text": "...",
  "hook_type": "pattern_interrupt"
}

3️⃣ Integrate into Story Adapter

Scene 1 must use selected hook.

✅ Success Criteria

✔ Scene 1 is clearly stronger
✔ Different runs feel different
✔ You can print hook rankings

🟢 DAY 9 — Persona System (Brand Consistency)
🎯 Objective

Stop generating “random tone” content.

What to Build
1️⃣ Persona definitions

Create:

app/intelligence/personas.py


Start with 2 personas only:

curious_kid

fast_explainer

Each persona defines:

sentence length

narration energy

vocabulary level

voice profile

2️⃣ Persona selection logic

Simple rules:

kids → curious_kid
facts → fast_explainer

3️⃣ Enforce persona in:

Story narration

Audio service

Visual prompts

✅ Success Criteria

✔ Same story feels different with persona swap
✔ Tone consistency across scenes

🟢 DAY 10 — Emotion Curve Engine (Pacing Control)
🎯 Objective

Control how the viewer feels per second.

What to Build
1️⃣ Emotion curve templates

Create:

app/intelligence/emotion_curves.py


Start with 2 curves:

curiosity → tension → surprise → loop

shock → explain → twist → loop

2️⃣ Scene ↔ emotion binding

Each scene must declare:

{
  "emotion": "curiosity"
}

3️⃣ Emotion-aware prompt shaping

Modify story prompts to reflect emotion.

✅ Success Criteria

✔ Pacing feels intentional
✔ No flat emotional sections

🟢 DAY 11 — Critic Upgrade (Smarter Judgment)
🎯 Objective

Make the system know why something is bad.

What to Improve
1️⃣ Add emotion alignment score

Check:

does hook emotion match curve?

does pacing degrade?

2️⃣ Structured critic output

Example:

{
  "hook_score": 0.8,
  "emotion_alignment": 0.7,
  "loop_strength": 0.9,
  "verdict": "retry"
}

3️⃣ Targeted retries

Retry only:

hook

or ending

Not the full story.

✅ Success Criteria

✔ Fewer retries
✔ Better retries
✔ Clear critic reasoning

🟢 DAY 12 — Creative Memory (v1 – Lightweight)
🎯 Objective

Stop forgetting what worked.

What to Build
1️⃣ Memory schema (simple)

Store:

top hooks

personas

emotion curves

scores

2️⃣ Reuse logic

If a hook scores > 0.85:

allow reuse with mutation

✅ Success Criteria

✔ Hooks reappear (with variation)
✔ Average score improves over batch

🟢 DAY 13 — Batch Intelligence & Evaluation
🎯 Objective

See improvement at scale.

What to Do
1️⃣ Generate 20 Shorts (same niche)

Log:

hook types

scores

retries

2️⃣ Compare vs Week 1

You should see:

higher average hook score

fewer retries

better endings

✅ Success Criteria

✔ Clear quality delta vs Week 1
✔ Patterns emerging

🟢 DAY 14 — Freeze, Refactor, Document
🎯 Objective

Stabilize before Week 3.

Tasks

Clean up interfaces

Document personas & hook types

Lock Week-2 feature set

Prepare demo batch

✅ Success Criteria

✔ System feels solid
✔ No feature creep
✔ Ready for scaling

🚀 End of Week 2 State

You now have:

✅ Hook intelligence
✅ Persona-based content
✅ Emotion-aware pacing
✅ Smarter critic
✅ First learning loop

At this point, your system is qualitatively better than generic AI video tools.