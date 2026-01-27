Week 27 Plan: Engine Refactoring and Hook System
Objective
Refactor existing engines to standardized interfaces and build hook generation capability. After this week, engines are independently replaceable, testable, and the system can generate optimized hooks that determine viral success.

Why This Week
Week 26 established reliability. Now the system is stable but not optimized for creator success. The engines work but lack the intelligence that separates average content from viral content. Hook quality determines 80% of video performance. Starting here gives maximum impact.

What To Build
Part 1: Engine Interface Standardization
Problem it solves: Current engines have inconsistent interfaces. Changing one engine requires understanding its specific implementation. Testing is difficult. Replacement is risky.

Standard engine interface:

Every engine must implement:

Input validation method
Execution method
Output validation method
Progress reporting method
Cancellation handling method
Resource cleanup method
Standard input structure:

Every engine receives:

Job context with identifiers and metadata
Engine-specific parameters as structured data
References to upstream artifacts
Quality requirements and thresholds
Timeout and resource limits
Standard output structure:

Every engine produces:

Primary artifact reference
Secondary artifacts if applicable
Execution metrics including duration and resource usage
Quality scores for output validation
Metadata for downstream engines
Engine registry:

Central registry that:

Lists all available engines
Provides engine capabilities and requirements
Enables engine discovery by type
Supports engine versioning
Tracks engine health and performance
Part 2: Script Engine Refactoring
Current state: Script engine generates full script as single unit. No separation of hook from body. No structure awareness.

Refactored capabilities:

Capability	Description
Segmented generation	Separate hook, body, CTA generation
Structure templates	Apply content structure patterns
Length targeting	Generate to specific duration
Variation generation	Produce multiple options
Quality scoring	Self-assess output quality
New script structure output:

Script output becomes structured data:

Hook segment with text, target duration, and hook type
Body segments as ordered list with text and target duration each
CTA segment with text, target duration, and CTA type
Full script as concatenated text
Estimated total duration
Segment count
Quality indicators
Script generation parameters:

Parameter	Purpose
content_topic	What the script is about
content_category	Fact, story, tutorial, motivation
hook_style	Curiosity, fear, promise, challenge, contrarian
structure_template	Template defining segment structure
target_duration	Desired total length in seconds
variation_count	How many script options to generate
tone	Educational, entertaining, controversial
Part 3: Hook Engine (New)
Purpose: Generate and optimize the opening 2-3 seconds that determine whether viewers continue watching.

Hook engine responsibilities:

Generate hook based on content and style
Apply proven hook templates
Score hook effectiveness
Generate variations for selection
Recommend visual pairing
Hook templates to implement:

Template Name	Structure	Example Pattern
Curiosity Gap	Statement creating unanswered question	"Nobody knows why [unexpected thing] happens"
Contrarian Claim	Challenge common belief	"Everything you believe about [topic] is wrong"
Fear Trigger	Warning or threat	"Stop doing [common action] immediately"
Secret Promise	Exclusive knowledge	"[Authority] never tells you this about [topic]"
Direct Challenge	Personal address	"You are [doing something wrong] right now"
Shocking Fact	Unexpected information	"[Surprising statistic] and it affects you"
Story Open	Narrative beginning	"In [year], something impossible happened"
Question Hook	Provocative question	"Why does [strange thing] actually happen"
Hook generation process:

Analyze content topic and category
Select appropriate hook templates
Generate hook using template structure
Score hook against effectiveness criteria
Generate alternative variations
Rank all hooks by predicted performance
Return top hooks with scores
Hook scoring criteria:

Criterion	Weight	Measurement
Curiosity creation	30%	Does it create unanswered question
Personal relevance	25%	Does it address viewer directly
Emotional trigger	20%	Does it provoke emotional response
Clarity	15%	Is it immediately understandable
Brevity	10%	Can it be delivered in 2 seconds
Hook output structure:

Primary hook text
Hook template used
Effectiveness score with breakdown
Alternative hooks as ranked list
Recommended visual type for hook
Recommended voice tone for hook
Part 4: Engine Orchestration Updates
Problem it solves: Current pipeline is linear. Adding new engines requires changing orchestration logic. No parallel execution.

Orchestration improvements:

Dependency declaration:
Each engine declares:

Required upstream engines
Optional upstream engines
Parallel execution compatibility
Resource requirements
Execution planning:
Orchestrator builds execution plan:

Determines engine order from dependencies
Identifies parallel execution opportunities
Allocates resources across engines
Estimates total execution time
Engine handoff protocol:
Standard handoff between engines:

Upstream engine produces artifact
Artifact is validated against schema
Artifact reference is passed to downstream
Downstream engine validates input before starting
Failure at any point triggers defined recovery
Part 5: Audio Engine Preparation
Why this week: Audio engine needs updates to support text overlay synchronization. Preparing interface now enables Week 28 work.

Interface additions needed:

Capability	Purpose
Word-level timestamps	Enable text sync
Segment markers	Align with script segments
Pacing parameters	Control speed and pauses
Emphasis markers	Highlight key words
Timestamp output structure:

Word list with start time, end time, and text for each word
Segment boundaries with segment ID, start time, and end time for each
Total duration
Words per minute calculated
Pause locations and durations
Audio generation parameters to add:

Parameter	Purpose
pacing_preset	Fast, medium, slow, dramatic
pause_at_segments	Insert pauses between segments
emphasis_words	Words to emphasize
speed_multiplier	Adjust overall speed
Database Concepts Needed
Engine registry table:

Engine identifier
Engine type
Engine version
Interface version
Capabilities list
Resource requirements
Health status
Last health check
Engine execution log table:

Execution identifier
Job reference
Engine identifier
Start timestamp
End timestamp
Input artifact references
Output artifact references
Quality scores
Resource usage metrics
Error details if failed
Hook template table:

Template identifier
Template name
Template category
Template structure pattern
Example hooks
Effectiveness baseline
Usage count
Success rate
Hook generation log table:

Generation identifier
Job reference
Content topic
Hook style requested
Template used
Generated hooks with scores
Selected hook
Timestamp
How To Think About It
Engines are the atoms of your system. Everything is built from engine outputs. If engines have inconsistent interfaces, every integration is custom work. If engines have standard interfaces, they become interchangeable components.

Hook optimization is not about better AI prompts. It is about encoding proven patterns into templates and scoring outputs against effectiveness criteria. The hook engine applies creator knowledge systematically.

Backend Capabilities Required
Engine Registry Operations
Register engine with capabilities
Get engine by type
Get engine by identifier
Update engine health status
List all engines with status
Get engine performance metrics
Engine Execution Operations
Validate engine input
Execute engine with monitoring
Validate engine output
Log execution metrics
Handle engine timeout
Clean up engine resources
Hook Generation Operations
Generate hook for content
Apply hook template
Score hook effectiveness
Generate hook variations
Get hook templates by category
Track hook performance
Script Generation Operations
Generate segmented script
Apply structure template
Generate script variations
Score script quality
Target specific duration
Validation Rules
Engine registration:

Engine must implement standard interface
Engine must pass health check
Engine version must be valid semver
Engine must not duplicate existing identifier
Engine execution:

Input must validate against engine schema
Timeout must be respected
Output must validate against engine schema
Resources must be released on completion
Hook generation:

Content topic must be provided
Hook style must be valid option
At least one hook must be generated
Hook must fit duration constraint
Script generation:

Target duration must be achievable
Structure template must be valid
All segments must have content
Total duration must be within tolerance
Success Criteria for Week 27
All engines implement standard interface with consistent input, output, and lifecycle methods. Engine registry tracks all engines with health and performance data. Script engine generates segmented output with hook, body, and CTA separated.

Hook engine generates hooks using template system. Hook scoring produces meaningful effectiveness predictions. Multiple hook variations are generated and ranked.

Orchestrator uses dependency declarations to plan execution. Engine handoffs use standard protocol. Execution logging captures metrics for all engine runs.

Audio engine interface is prepared for timestamp output. Pacing parameters are defined and documented.

Files To Create
File	Purpose
app/engines/base.py	Standard engine interface definition
app/engines/registry.py	Engine registration and discovery
app/engines/orchestrator.py	Execution planning and coordination
app/engines/hook_engine.py	Hook generation and scoring
app/engines/hook_templates.py	Hook template definitions
app/engines/script_engine.py	Refactored script generation
app/api/engine_routes.py	Engine management endpoints
API Endpoints To Implement
Endpoint	Method	Description
/v1/engines/	GET	List all engines
/v1/engines/{id}	GET	Get engine details
/v1/engines/{id}/health	GET	Get engine health
/v1/engines/{id}/metrics	GET	Get engine performance
/v1/hooks/generate	POST	Generate hooks for content
/v1/hooks/templates	GET	List hook templates
/v1/hooks/templates/{id}	GET	Get template details
/v1/hooks/score	POST	Score a hook
/v1/scripts/generate	POST	Generate segmented script
/v1/scripts/structures	GET	List structure templates
Integration Points
With Reliability System (Week 26):
Engine execution integrates with checkpointing. Each engine completion is checkpoint opportunity. Engine failures trigger retry logic.

With Template System (Week 25):
Templates specify engine configurations. Hook style and structure template come from project template.

With Batch System (Week 24):
Batch items share engine configurations. Hook engine can generate variations across batch for testing.

With Quality Validation (Week 23):
Engine outputs are validated against quality thresholds. Hook scores feed into overall quality assessment.

What This Enables
After Week 27, Story-Genius has modular engines that can be independently improved, replaced, and tested. Hook generation applies proven viral patterns to content. Script structure follows templates that encode creator knowledge.

The system moves from generating videos to generating optimized content. Each component contributes measurably to output quality.

