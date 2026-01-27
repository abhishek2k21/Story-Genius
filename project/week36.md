Week 36 Plan: Caption Export
Objective
Build subtitle and caption generation system with SRT and VTT export, accurate word-level timing, multi-language structure preparation, styling options, and accessibility compliance. After this week, every video has professional captions ready for platform upload and accessibility requirements.

Why This Week
Captions are no longer optional. Platforms prioritize accessible content. 85% watch without sound. Auto-captions are often inaccurate. Professional creators provide their own captions. Caption export transforms Story-Genius outputs from videos into complete, accessible content packages.

Day-by-Day Breakdown
Monday: Caption Data Model and Timing Extraction
Focus: Build caption data structures and extract accurate timing from audio engine.

What to build:

Caption model:

Field	Type	Purpose
caption_id	UUID	Unique identifier
project_id	UUID	Parent project
audio_artifact_id	UUID	Source audio
language_code	string	ISO 639-1 code
caption_type	enum	subtitle, closed_caption
status	enum	processing, ready, failed
cue_count	integer	Number of caption cues
total_duration	float	Total caption duration
word_count	integer	Total words
created_at	timestamp	Generation time
updated_at	timestamp	Last modification
Caption cue model:

Field	Type	Purpose
cue_id	UUID	Unique identifier
caption_id	UUID	Parent caption
cue_index	integer	Sequence number
start_time	float	Start in seconds
end_time	float	End in seconds
text	string	Caption text
words	list	Word-level timing
speaker_id	string	Speaker identifier if multiple
style_id	string	Style reference
position	object	Custom positioning
Word timing model:

Field	Type	Purpose
word	string	The word
start_time	float	Word start
end_time	float	Word end
confidence	float	Recognition confidence
Timing extraction from audio:

Source	Method
Text overlay engine	Use existing word timestamps
Audio artifact	Extract if not available
Script segments	Align with audio
Timing accuracy requirements:

Requirement	Value
Word alignment	Within 50ms
Cue start	Within 100ms of speech
Cue end	Within 100ms of speech end
Gap handling	Minimum 100ms between cues
Cue generation rules:

Rule	Value	Reasoning
Maximum characters per line	42	Readability
Maximum lines per cue	2	Screen space
Maximum cue duration	7 seconds	Comprehension
Minimum cue duration	1 second	Readability
Reading speed	150-200 WPM	Comfortable pace
Deliverables for Monday:

Caption and cue models
Word timing extraction
Cue generation from words
Timing validation
Duration calculations
Tuesday: SRT Format Export
Focus: Build SRT (SubRip) format generation with proper formatting and validation.

What to build:

SRT format specification:

1
00:00:01,000 --> 00:00:04,500
First caption cue text
goes here on one or two lines

2
00:00:05,000 --> 00:00:08,200
Second caption cue text
SRT components:

Component	Format
Cue number	Sequential integer starting at 1
Timestamp	HH:MM:SS,mmm (comma for milliseconds)
Arrow	" --> " with spaces
Text	One or two lines, blank line after
SRT generation process:

Load caption cues in order
Format each cue number
Format start timestamp
Format end timestamp
Format text with line breaks
Join with proper spacing
Validate output
Timestamp formatting:

Input	Output Format
1.5 seconds	00:00:01,500
65.25 seconds	00:01:05,250
3723.1 seconds	01:02:03,100
Text formatting rules:

Rule	Implementation
Line breaks	Insert at word boundaries
Max line length	42 characters
Max lines	2 per cue
Character encoding	UTF-8
Special characters	Escape as needed
SRT validation:

Check	Validation
Sequential numbers	1, 2, 3, ...
Timestamp order	Each start > previous end
No overlap	Cues don't overlap
Valid timestamps	Proper format
Non-empty text	Each cue has content
SRT export options:

Option	Description
include_styling	Add basic styling tags
line_length	Override max line length
merge_short_cues	Combine brief cues
split_long_cues	Break long cues
Deliverables for Tuesday:

SRT format generator
Timestamp formatter
Text line breaker
SRT validator
Export options handling
Wednesday: VTT Format Export
Focus: Build WebVTT format generation with styling, positioning, and metadata support.

What to build:

VTT format specification:

WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:04.500
First caption cue text
goes here on one or two lines

00:00:05.000 --> 00:00:08.200 align:center position:50%
Second caption cue with positioning
VTT components:

Component	Format
Header	WEBVTT required first line
Metadata	Optional key: value pairs
Timestamp	HH:MM:SS.mmm (period for milliseconds)
Settings	Optional cue settings after timestamp
Text	One or more lines
VTT header metadata:

Metadata	Purpose
Kind	captions, subtitles, descriptions
Language	ISO language code
Title	Optional title
VTT cue settings:

Setting	Values	Purpose
align	start, center, end, left, right	Text alignment
position	0%-100%	Horizontal position
line	number or percentage	Vertical position
size	0%-100%	Cue box width
vertical	rl, lr	Vertical text
VTT styling:

Tag	Purpose	Example
<b>	Bold	<b>Important</b>
<i>	Italic	<i>Emphasis</i>
<u>	Underline	<u>Underlined</u>
<c.classname>	CSS class	<c.speaker1>Text</c>
<v Speaker>	Voice/speaker	<v John>Hello</v>
VTT generation process:

Write WEBVTT header
Add metadata if provided
Add blank line
For each cue:
Format timestamps
Add settings if specified
Format styled text
Add blank line separator
Validate output
VTT vs SRT differences:

Aspect	SRT	VTT
Millisecond separator	Comma	Period
Cue numbers	Required	Optional
Styling	Limited	Full CSS support
Positioning	Not supported	Supported
Metadata	Not supported	Supported
VTT export options:

Option	Description
include_styling	Add styling tags
include_positioning	Add position settings
include_speaker	Add voice tags
style_preset	Predefined style set
Deliverables for Wednesday:

VTT format generator
VTT timestamp formatter
Styling tag application
Positioning settings
VTT validator
Export options handling
Thursday: Caption Styling and Accessibility
Focus: Build styling presets and ensure accessibility compliance.

What to build:

Style preset model:

Field	Type	Purpose
preset_id	UUID	Unique identifier
name	string	Preset name
font_family	string	Font specification
font_size	string	Size in percentage
font_color	string	Text color
background_color	string	Background color
background_opacity	float	Background transparency
text_align	enum	Alignment
position	enum	Default position
is_system	boolean	System preset
System style presets:

Preset	Description
default	White text, semi-transparent black background
high_contrast	Yellow text, black background
minimal	White text, no background
boxed	White text, solid black background
bottom_bar	Full-width background bar
Accessibility requirements:

Requirement	Implementation
Contrast ratio	Minimum 4.5:1 for normal text
Font size	Minimum readable size
Timing	Adequate reading time
Completeness	All spoken content captioned
Speaker identification	Multiple speakers identified
Accessibility validation:

Check	Validation
Contrast	Calculate contrast ratio
Reading speed	WPM within acceptable range
Cue duration	Minimum display time
Completeness	Coverage of audio duration
Accuracy	Word error rate if reference available
Speaker identification:

Field	Purpose
speaker_id	Unique speaker identifier
speaker_name	Display name
speaker_style	Style for this speaker
Speaker formatting options:

Option	Example
prefix	[John]: Hello
voice_tag	<v John>Hello</v>
style_class	<c.john>Hello</c>
color_coded	Different color per speaker
Closed caption specific features:

Feature	Description
Sound descriptions	[music playing], [door slams]
Speaker changes	Indicate speaker switches
Non-speech audio	[laughter], [applause]
Music lyrics	♪ Lyrics here ♪
Sound description model:

Field	Type	Purpose
description_type	enum	music, sound_effect, ambient
text	string	Description text
start_time	float	Start time
end_time	float	End time
Deliverables for Thursday:

Style preset model and system presets
Accessibility validation
Contrast ratio calculator
Speaker identification
Sound description support
Closed caption features
Friday: Multi-Language Structure and Translation Preparation
Focus: Build structure for multi-language support and translation workflow preparation.

What to build:

Multi-language caption model:

Field	Type	Purpose
caption_set_id	UUID	Groups all languages
project_id	UUID	Parent project
primary_language	string	Source language
available_languages	list	All language codes
created_at	timestamp	Creation time
Language-specific caption:

Field	Type	Purpose
caption_id	UUID	Unique identifier
caption_set_id	UUID	Parent set
language_code	string	ISO 639-1 code
language_name	string	Display name
is_primary	boolean	Source language
is_auto_translated	boolean	Machine translated
translation_status	enum	pending, complete, reviewed
translator_notes	text	Notes for translators
Supported languages (initial set):

Code	Language
en	English
es	Spanish
pt	Portuguese
fr	French
de	German
it	Italian
nl	Dutch
pl	Polish
ru	Russian
ja	Japanese
ko	Korean
zh	Chinese
ar	Arabic
hi	Hindi
Translation preparation:

Feature	Purpose
Export for translation	Generate translation-ready file
Import translation	Load translated captions
Timing preservation	Keep original timing
Character expansion	Allow for longer translations
Translation file format:

Format	Use Case
XLIFF	Professional translation tools
CSV	Simple spreadsheet editing
JSON	Developer-friendly
Translation-ready export structure:

Field	Purpose
cue_id	Reference for reimport
source_text	Original text
target_text	Empty for translation
context	Surrounding cues for context
max_length	Character limit recommendation
notes	Translator guidance
Character expansion rules:

Source	Target	Expansion
English	German	+30%
English	French	+20%
English	Spanish	+25%
English	Japanese	-10%
English	Chinese	-20%
Timing adjustment for translation:

Approach	Description
Preserve timing	Keep original timing, text may wrap
Adjust duration	Extend cue if needed
Split cues	Break into smaller cues
Adjust reading speed	Allow faster reading
Deliverables for Friday:

Multi-language caption model
Language configuration
Translation export formats
Translation import handling
Character expansion calculation
Timing adjustment logic
Saturday: API Endpoints and Testing
Focus: Expose caption capabilities via API and comprehensive testing.

What to build:

API endpoints:

Endpoint	Method	Description
/v1/captions/generate	POST	Generate captions from audio
/v1/captions/{id}	GET	Get caption details
/v1/captions/{id}	PUT	Update caption
/v1/captions/{id}	DELETE	Delete caption
/v1/captions/{id}/cues	GET	List all cues
/v1/captions/{id}/cues/{cue_id}	PUT	Update specific cue
/v1/captions/{id}/export/srt	GET	Export as SRT
/v1/captions/{id}/export/vtt	GET	Export as VTT
/v1/captions/{id}/export/translation	GET	Export for translation
/v1/captions/{id}/import/translation	POST	Import translation
/v1/captions/{id}/validate	GET	Validate accessibility
/v1/captions/{id}/languages	GET	List available languages
/v1/captions/{id}/languages	POST	Add language
/v1/captions/{id}/languages/{lang}	GET	Get language version
/v1/captions/{id}/languages/{lang}	DELETE	Remove language
/v1/captions/styles	GET	List style presets
/v1/captions/styles/{id}	GET	Get style details
/v1/captions/styles	POST	Create custom style
/v1/projects/{id}/captions	GET	Get project captions
/v1/projects/{id}/captions	POST	Generate for project
Request structure for generation:

Field	Required	Description
project_id	Yes	Source project
language_code	No	Language (default: en)
caption_type	No	subtitle or closed_caption
style_preset	No	Style to apply
include_sound_descriptions	No	For closed captions
max_line_length	No	Override default
max_lines_per_cue	No	Override default
Response structure for caption:

Field	Description
caption_id	Unique identifier
project_id	Parent project
language_code	Caption language
caption_type	Type of caption
status	Processing status
cue_count	Number of cues
total_duration	Caption duration
accessibility_score	Compliance score
available_formats	Export formats
Request structure for export:

Field	Required	Description
format	Yes	srt, vtt, xliff, csv, json
include_styling	No	Add styling (VTT only)
include_positioning	No	Add positions (VTT only)
style_preset	No	Override style
Testing requirements:

Test Category	Coverage
Timing extraction	Accuracy from audio
Cue generation	Line breaking, duration
SRT export	Format compliance
VTT export	Format compliance
Styling	All presets
Accessibility	All validation rules
Multi-language	All supported languages
Translation	Export and import
Integration	Full workflow
Validation tests:

SRT files parse in standard players
VTT files parse in browsers
Timing aligns with audio
Cues are readable at display speed
Accessibility requirements met
Multi-language structure correct
Translation import preserves timing
Deliverables for Saturday:

All API endpoints implemented
Request and response validation
Comprehensive test suite
Format compliance validation
Documentation for captions
Database Concepts Needed
Caption sets table:

caption_set_id UUID primary key
project_id foreign key
primary_language varchar not null
available_languages JSONB
created_at timestamp
updated_at timestamp
Captions table:

caption_id UUID primary key
caption_set_id foreign key
project_id foreign key
audio_artifact_id foreign key
language_code varchar not null
language_name varchar
caption_type enum not null
is_primary boolean default false
is_auto_translated boolean default false
translation_status enum
status enum not null
cue_count integer
total_duration float
word_count integer
style_preset_id foreign key
accessibility_score float
translator_notes text
created_at timestamp
updated_at timestamp
Caption cues table:

cue_id UUID primary key
caption_id foreign key
cue_index integer not null
start_time float not null
end_time float not null
text text not null
words JSONB
speaker_id varchar
style_id varchar
position JSONB
is_sound_description boolean default false
created_at timestamp
updated_at timestamp
Caption style presets table:

preset_id UUID primary key
user_id foreign key nullable
name varchar not null
font_family varchar
font_size varchar
font_color varchar
background_color varchar
background_opacity float
text_align enum
position enum
is_system boolean default false
created_at timestamp
Indexes needed:

caption_sets(project_id)
captions(caption_set_id)
captions(project_id, language_code)
caption_cues(caption_id, cue_index)
caption_style_presets(user_id)
Files To Create
File	Purpose
app/captions/models.py	Caption, Cue, Style models
app/captions/timing.py	Timing extraction and processing
app/captions/cue_generator.py	Cue generation from words
app/captions/srt.py	SRT format export
app/captions/vtt.py	VTT format export
app/captions/styling.py	Style presets and application
app/captions/accessibility.py	Accessibility validation
app/captions/languages.py	Multi-language support
app/captions/translation.py	Translation workflow
app/captions/service.py	Main caption service
app/api/caption_routes.py	API endpoints
tests/test_captions.py	Comprehensive tests
Success Criteria for Week 36
Captions generate accurately from audio with word-level timing. Cues break properly at line length limits. Reading speed is comfortable for viewers.

SRT export produces valid files that work in standard video players. VTT export produces valid files that work in web browsers. Styling applies correctly in VTT.

Style presets cover common use cases. Custom styles can be created. Accessibility validation catches compliance issues.

Multi-language structure supports 14+ languages. Translation export produces usable files. Translation import preserves timing.

Every video can have professional captions in multiple languages.

Integration Points
With Text Overlay Engine (Week 28):
Reuse word-level timestamps for caption timing.

With Audio Engine:
Extract timing if not available from text overlay.

With Project System:
Captions are associated with projects.

With Asset Library (Week 33):
Caption files can be stored as assets.

With Batch System (Week 24):
Batch caption generation for multiple videos.

What This Enables
After Week 36, Story-Genius produces accessible content. Every video has SRT and VTT captions available. Captions meet accessibility requirements. Multi-language support enables global reach.

Creators upload captions alongside videos, improving discoverability and compliance. The 85% who watch without sound get complete content through captions.
