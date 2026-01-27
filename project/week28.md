Week 28 Plan: Text Overlay Engine and Audio Synchronization
Objective
Build text overlay engine that synchronizes with word-level audio timestamps, respects platform-specific safe zones, and ensures content is fully comprehensible without sound. After this week, every video works for the 85% of viewers who watch silently.

Why This Week
Hook engine creates compelling openings. Script engine structures content properly. But if viewers cannot read the content while scrolling silently, none of that matters. Text overlay is not decoration. It is the primary content delivery mechanism for most viewers.

Day-by-Day Breakdown
Monday: Audio Engine Timestamp Extraction
Focus: Upgrade audio engine to output word-level timing data.

What to build:

Timestamp extraction capability:

Extract start time for each word
Extract end time for each word
Calculate word duration
Identify natural pause points
Mark segment boundaries
Timestamp output structure:

Field	Type	Purpose
word	string	The spoken word
start_time	float	Start in seconds
end_time	float	End in seconds
duration	float	Word duration
confidence	float	Recognition confidence
is_segment_start	boolean	Marks segment boundary
is_emphasis	boolean	Marks emphasized word
Word grouping logic:

Group words into phrases for display
Maximum 5-7 words per display group
Break at natural pause points
Break at punctuation
Respect segment boundaries
Phrase output structure:

Field	Type	Purpose
phrase_id	integer	Sequence number
text	string	Grouped words
start_time	float	First word start
end_time	float	Last word end
word_count	integer	Words in phrase
segment_id	string	Parent segment reference
Deliverables for Monday:

Timestamp extraction method in audio engine
Phrase grouping algorithm
Unit tests for timestamp accuracy
Integration with existing audio generation
Tuesday: Safe Zone Configuration System
Focus: Build platform-aware safe zone definitions and text positioning logic.

What to build:

Safe zone definitions per platform:

Platform	Top Margin	Bottom Margin	Left Margin	Right Margin
YouTube Shorts	150px	180px	40px	40px
Instagram Reels	120px	250px	40px	40px
TikTok	100px	150px	40px	40px
YouTube Long	60px	80px	100px	100px
Safe zone reasoning:

Top margin avoids platform UI elements
Bottom margin avoids engagement buttons and captions
Side margins ensure readability on all devices
Values are percentage-convertible for different resolutions
Text position options:

Position	Vertical Placement	Use Case
top_safe	Below top margin	Secondary information
center	Vertical center	Primary content
lower_third	Above bottom margin	Main text overlay
bottom_safe	Just above bottom margin	CTA and captions
Position calculation logic:

Input platform and position preference
Calculate pixel coordinates from safe zone
Adjust for resolution differences
Return absolute positioning
Text area calculation:

Calculate available width within margins
Calculate available height for text region
Determine maximum font size for readability
Ensure minimum touch target spacing
Deliverables for Tuesday:

Safe zone configuration module
Position calculation functions
Resolution-aware coordinate conversion
Platform preset validation
Wednesday: Text Overlay Timing Engine
Focus: Build core timing logic that maps phrases to display windows.

What to build:

Display timing rules:

Rule	Value	Reasoning
Minimum display time	0.8 seconds	Reading speed floor
Maximum display time	4.0 seconds	Attention span limit
Words per second readable	3-4 words	Average reading speed
Transition buffer	0.1 seconds	Smooth transitions
Early appearance	0.1 seconds before audio	Anticipation
Timing calculation process:

Receive phrase list with audio timestamps
Calculate raw display window from audio timing
Apply minimum display time rule
Apply maximum display time rule
Add early appearance offset
Add transition buffer between phrases
Validate no overlapping display windows
Resolve conflicts by adjusting adjacent phrases
Conflict resolution logic:

If phrases overlap, extend first phrase end
If gap is too small, merge into single phrase
If phrase is too long, split at natural break
Preserve segment boundary markers
Timing output structure:

Field	Type	Purpose
phrase_id	integer	Reference to phrase
text	string	Display text
display_start	float	When to show
display_end	float	When to hide
audio_start	float	When audio begins
audio_end	float	When audio ends
position	string	Where to display
transition_in	string	Entry animation type
transition_out	string	Exit animation type
Deliverables for Wednesday:

Timing calculation engine
Conflict resolution algorithm
Timing validation methods
Display timeline generator
Thursday: Text Style and Animation System
Focus: Build text styling and animation parameters for overlay rendering.

What to build:

Text style presets:

Preset Name	Font Weight	Background	Use Case
clean	Bold	None	Minimal aesthetic
boxed	Bold	Semi-transparent black	High contrast
outlined	Bold with stroke	None	Versatile
gradient	Bold	Gradient background	Trendy
minimal	Regular	None	Subtle
Style parameters:

Parameter	Options	Default
font_family	Sans-serif options	System default
font_size	Auto-calculated or fixed	Auto
font_weight	Regular, Medium, Bold	Bold
text_color	Hex color	#FFFFFF
stroke_color	Hex color	#000000
stroke_width	0-5 pixels	2
background_color	Hex with alpha	None
background_padding	Pixels	10
text_align	Left, Center, Right	Center
line_height	Multiplier	1.2
Animation types:

Animation	Description	Duration
fade_in	Opacity 0 to 1	0.15s
fade_out	Opacity 1 to 0	0.15s
pop_in	Scale 0.8 to 1 with fade	0.2s
slide_up	Translate Y with fade	0.2s
typewriter	Character by character	Variable
none	Instant appear/disappear	0s
Word highlighting:

Highlight current word being spoken
Highlight color parameter
Highlight style options
Timing sync with audio timestamps
Deliverables for Thursday:

Style preset definitions
Style parameter validation
Animation configuration system
Word highlight logic
Friday: Text Overlay Engine Integration
Focus: Combine all components into unified text overlay engine.

What to build:

Text overlay engine interface:

Inputs:

Audio artifact with timestamps
Script with segments
Platform target
Style preset or custom parameters
Position preference
Animation preferences
Outputs:

Text overlay timeline
Positioned phrase list
Style parameters per phrase
Animation keyframes
Render instructions
Engine execution flow:

Validate inputs against schema
Extract phrases from audio timestamps
Calculate safe zone for platform
Determine positions for each phrase
Calculate display timing
Apply style preset
Generate animation parameters
Produce render instructions
Validate output completeness
Render instruction format:

Field	Purpose
frame_range	Start and end frame numbers
text	Content to display
position_x	Horizontal coordinate
position_y	Vertical coordinate
style	Complete style parameters
animation	Animation keyframes
layer	Z-index for compositing
Integration with video engine:

Text engine produces render instructions
Video engine consumes instructions during composition
No direct coupling between engines
Standard artifact format for handoff
Deliverables for Friday:

Complete text overlay engine
Standard engine interface implementation
Engine registration in registry
Integration tests with audio engine
Sample render instruction output
Saturday: API Endpoints and Testing
Focus: Expose text overlay capabilities via API and comprehensive testing.

What to build:

API endpoints:

Endpoint	Method	Description
/v1/text/overlay/generate	POST	Generate overlay from audio
/v1/text/overlay/preview	POST	Preview overlay timing
/v1/text/safe-zones	GET	List platform safe zones
/v1/text/safe-zones/{platform}	GET	Get specific safe zone
/v1/text/styles	GET	List style presets
/v1/text/styles/{name}	GET	Get style details
/v1/text/animations	GET	List animation types
/v1/text/validate	POST	Validate overlay configuration
Request structure for generation:

Field	Required	Description
audio_artifact_id	Yes	Reference to audio with timestamps
platform	Yes	Target platform
style_preset	No	Style preset name
custom_style	No	Override style parameters
position	No	Position preference
animation_in	No	Entry animation
animation_out	No	Exit animation
highlight_words	No	Enable word highlighting
Response structure:

Field	Description
overlay_id	Generated overlay identifier
phrase_count	Number of text phrases
total_duration	Timeline duration
render_instructions	Full instruction set
preview_url	Optional preview endpoint
Testing requirements:

Test Category	Coverage
Unit tests	Each component function
Integration tests	Full pipeline flow
Platform tests	Each platform safe zone
Style tests	Each style preset
Animation tests	Each animation type
Edge cases	Empty audio, single word, very long phrases
Performance tests	Large script processing time
Validation tests:

Timestamps align with audio
No overlapping display windows
All text within safe zones
Style parameters are valid
Animations have correct duration
Deliverables for Saturday:

All API endpoints implemented
Request/response validation
Comprehensive test suite
Documentation for endpoints
Example usage scripts
Database Concepts Needed
Text overlay table:

Overlay identifier
Audio artifact reference
Platform target
Style configuration
Position configuration
Animation configuration
Generated timestamp
Phrase count
Total duration
Text overlay phrases table:

Phrase identifier
Overlay reference
Sequence number
Text content
Display start time
Display end time
Position coordinates
Style overrides if any
Style preset table:

Preset identifier
Preset name
Style parameters as structured data
Is system preset flag
Creator reference if custom
Usage count
Files To Create
File	Purpose
app/engines/text_overlay/engine.py	Main text overlay engine
app/engines/text_overlay/timing.py	Timing calculation logic
app/engines/text_overlay/positioning.py	Safe zones and positioning
app/engines/text_overlay/styling.py	Style presets and parameters
app/engines/text_overlay/animation.py	Animation definitions
app/engines/text_overlay/renderer.py	Render instruction generator
app/engines/audio_engine.py	Updated with timestamp extraction
app/api/text_routes.py	API endpoints
tests/test_text_overlay.py	Comprehensive tests
Success Criteria for Week 28
Audio engine produces accurate word-level timestamps with phrase grouping. Safe zones are correctly defined for all supported platforms. Text positioning respects safe zones on all resolutions.

Timing engine produces non-overlapping display windows. Style presets produce visually consistent results. Animations are smooth and correctly timed.

Text overlay engine integrates with standard engine interface. API endpoints expose all text overlay capabilities. Tests cover all components and edge cases.

Video can be watched without sound and fully understood through text overlays.

Integration Points
With Audio Engine (Week 27 prepared):
Audio engine now outputs timestamp data that text engine consumes.

With Video Engine:
Text engine produces render instructions that video engine applies during composition.

With Template System (Week 25):
Templates can specify text style preset and position preferences.

With Format System (Week 20):
Safe zones are derived from format specifications.

With Batch System (Week 24):
Batch items share text style configuration for consistency.

What This Enables
After Week 28, Story-Genius produces videos that work for silent viewing. Text appears at correct moments, stays readable long enough, and never gets hidden by platform UI. Creators can trust that their content reaches the 85% majority who scroll without sound.

