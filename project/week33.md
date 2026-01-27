Week 33 Plan: Asset Library
Objective
Build asset management system with upload, organization, versioning, and referencing capabilities. After this week, creators can upload images, audio, logos, and other media once and reuse them across unlimited projects.

Why This Week
Currently, every project requires fresh asset references. Creators cannot build a personal library of brand assets, intro clips, music tracks, or visual elements. This creates repetitive work and inconsistent branding. Asset library transforms Story-Genius from project-based to creator-based workflow.

Day-by-Day Breakdown
Monday: Asset Model and Storage Foundation
Focus: Build asset data model and storage infrastructure for various asset types.

What to build:

Asset types supported:

Type	Extensions	Max Size	Use Cases
image	jpg, png, webp, gif	10MB	Thumbnails, overlays, backgrounds
audio	mp3, wav, m4a	50MB	Music, sound effects, intros
video	mp4, mov, webm	200MB	Clips, intros, outros
font	ttf, otf, woff	5MB	Custom typography
logo	png, svg	5MB	Branding, watermarks
Asset model structure:

Field	Type	Purpose
asset_id	UUID	Unique identifier
user_id	UUID	Owner reference
name	string	User-defined name
description	string	Optional description
asset_type	enum	image, audio, video, font, logo
mime_type	string	Exact MIME type
file_extension	string	Original extension
file_size	integer	Size in bytes
storage_path	string	Internal storage location
original_filename	string	Upload filename
checksum	string	SHA-256 for deduplication
status	enum	processing, ready, failed, deleted
metadata	JSON	Type-specific metadata
created_at	timestamp	Upload time
updated_at	timestamp	Last modification
Type-specific metadata:

Image metadata:

Field	Purpose
width	Pixel width
height	Pixel height
format	Image format
color_space	RGB, CMYK
has_transparency	Alpha channel present
Audio metadata:

Field	Purpose
duration_seconds	Length
sample_rate	Audio quality
channels	Mono, stereo
bitrate	Quality indicator
Video metadata:

Field	Purpose
duration_seconds	Length
width	Frame width
height	Frame height
fps	Frame rate
codec	Video codec
has_audio	Audio track present
Storage structure:

/storage/assets/{user_id}/{asset_type}/{year}/{month}/{asset_id}.{ext}
Storage requirements:

User isolation at directory level
Organized by type and date
Original preserved, derivatives generated
Backup-friendly structure
Deliverables for Monday:

Asset model and database schema
Storage path generation
Type validation utilities
Metadata extraction foundations
Checksum calculation
Tuesday: Upload Processing Pipeline
Focus: Build upload handling with validation, processing, and metadata extraction.

What to build:

Upload flow:

Client initiates upload
Server validates file type and size
Server generates temporary storage path
File streams to temporary location
Validation runs on complete file
Metadata extracted based on type
Checksum calculated
File moved to permanent storage
Asset record created
Thumbnails/previews generated async
Upload validation rules:

Validation	Check	Error
File size	Under type limit	File too large
File type	Allowed extension	Invalid file type
MIME type	Matches extension	MIME mismatch
File integrity	Complete upload	Incomplete upload
Malware scan	Clean file	Security violation
Image processing:

Process	Purpose
Resize validation	Within reasonable dimensions
Format validation	Supported format
Thumbnail generation	150x150 preview
Medium preview	600px max dimension
Metadata extraction	Dimensions, format, transparency
Audio processing:

Process	Purpose
Duration extraction	Length calculation
Format validation	Supported codec
Waveform generation	Visual preview
Sample generation	10-second preview clip
Metadata extraction	Duration, bitrate, channels
Video processing:

Process	Purpose
Duration extraction	Length calculation
Format validation	Supported codec
Thumbnail extraction	Frame at 25% duration
Preview generation	Low-res preview clip
Metadata extraction	Duration, dimensions, fps
Processing status flow:

Status	Meaning
processing	Upload received, processing
ready	Fully processed, usable
failed	Processing failed
deleted	Soft deleted
Deliverables for Tuesday:

Upload endpoint with streaming
File validation utilities
Image metadata extractor
Audio metadata extractor
Video metadata extractor
Thumbnail generation
Wednesday: Asset Organization System
Focus: Build folder structure, tagging, and search capabilities for asset organization.

What to build:

Folder model:

Field	Type	Purpose
folder_id	UUID	Unique identifier
user_id	UUID	Owner reference
parent_folder_id	UUID	Parent folder, nullable for root
name	string	Folder name
description	string	Optional description
color	string	UI color hint
asset_count	integer	Cached count
created_at	timestamp	Creation time
updated_at	timestamp	Last modification
Folder operations:

Operation	Description
Create folder	New folder in parent
Rename folder	Change folder name
Move folder	Change parent
Delete folder	Remove folder and contents
List contents	Assets and subfolders
Folder rules:

Maximum depth of 5 levels
Unique names within same parent
Cannot delete folder with assets unless forced
Root folder implicit per user
Tag model:

Field	Type	Purpose
tag_id	UUID	Unique identifier
user_id	UUID	Owner reference
name	string	Tag name
color	string	UI color hint
usage_count	integer	Cached count
created_at	timestamp	Creation time
Asset-tag relationship:

Many-to-many relationship
Asset can have unlimited tags
Tag can apply to unlimited assets
Tag operations:

Operation	Description
Create tag	New tag for user
Rename tag	Change tag name
Delete tag	Remove tag, unlink from assets
Add to asset	Link tag to asset
Remove from asset	Unlink tag from asset
Bulk tag	Apply tag to multiple assets
Search capabilities:

Search Field	Type	Example
name	Text search	"logo"
asset_type	Enum filter	image
folder_id	UUID filter	Specific folder
tags	List filter	["brand", "intro"]
created_after	Date filter	Last 30 days
created_before	Date filter	Before date
file_size_min	Integer filter	Over 1MB
file_size_max	Integer filter	Under 10MB
Search response:

Paginated results
Sort options: name, date, size, type
Facet counts by type and folder
Deliverables for Wednesday:

Folder model and operations
Tag model and operations
Asset-folder relationship
Asset-tag relationship
Search service with filters
Pagination and sorting
Thursday: Asset Versioning System
Focus: Build version tracking for assets to maintain history and enable rollback.

What to build:

Version model:

Field	Type	Purpose
version_id	UUID	Unique identifier
asset_id	UUID	Parent asset reference
version_number	integer	Sequential version
storage_path	string	Version file location
file_size	integer	Version file size
checksum	string	Version checksum
metadata	JSON	Version-specific metadata
change_description	string	What changed
created_at	timestamp	Version creation time
created_by	UUID	User who created version
Versioning behavior:

Action	Result
Upload new version	Creates version record, updates asset
View history	Lists all versions
Download version	Gets specific version file
Rollback	Sets older version as current
Delete version	Removes specific version
Version limits:

Maximum 10 versions per asset
Oldest versions auto-pruned when limit exceeded
Current version never auto-deleted
Deleted versions recover storage
Current version tracking:

Asset record always points to current version. Version changes update asset metadata and storage_path.

Version comparison:

Capability	Purpose
Metadata diff	Show what changed
Size comparison	Track file size changes
Visual comparison	Side-by-side for images
Duplicate detection:

When uploading:

Calculate checksum
Check if checksum exists for user
If exists, offer to link existing asset
If different, proceed with upload
Deliverables for Thursday:

Version model and schema
Version creation on upload
Version history retrieval
Version rollback logic
Version pruning automation
Duplicate detection
Friday: Asset Referencing and Usage Tracking
Focus: Build system for referencing assets in projects and tracking usage across the platform.

What to build:

Asset reference model:

Field	Type	Purpose
reference_id	UUID	Unique identifier
asset_id	UUID	Referenced asset
resource_type	string	project, template, batch
resource_id	UUID	Referencing resource
usage_type	string	thumbnail, background, audio, etc.
created_at	timestamp	When reference created
Reference tracking benefits:

Know where asset is used
Prevent deletion of in-use assets
Usage analytics
Impact analysis for changes
Usage types by resource:

Resource	Usage Types
Project	thumbnail, background, overlay, audio, intro, outro
Template	default_thumbnail, default_audio, logo
Batch	shared_asset
Deletion protection:

When deleting asset:

Check for active references
If references exist, prevent deletion
Return list of referencing resources
Offer force delete option
Force delete removes references
Usage statistics:

Statistic	Purpose
Total references	Popularity indicator
Reference by type	Usage pattern
Recent uses	Activity tracking
Projects using	Impact scope
Asset URL generation:

URL Type	Purpose	Expiration
Permanent	Internal reference	None
Signed	External access	Configurable
Thumbnail	Quick preview	Long-lived
Download	Original file	Short-lived
Signed URL parameters:

Asset ID
Expiration timestamp
User ID
Signature hash
Deliverables for Friday:

Reference tracking model
Reference creation on project save
Reference cleanup on project delete
Usage statistics calculation
URL generation utilities
Deletion protection logic
Saturday: API Endpoints and Testing
Focus: Expose asset library capabilities via API and comprehensive testing.

What to build:

API endpoints:

Endpoint	Method	Description
/v1/assets/upload	POST	Upload new asset
/v1/assets	GET	List assets with filters
/v1/assets/{id}	GET	Get asset details
/v1/assets/{id}	PUT	Update asset metadata
/v1/assets/{id}	DELETE	Delete asset
/v1/assets/{id}/download	GET	Download asset file
/v1/assets/{id}/versions	GET	List versions
/v1/assets/{id}/versions	POST	Upload new version
/v1/assets/{id}/versions/{v}	GET	Get version details
/v1/assets/{id}/versions/{v}/rollback	POST	Rollback to version
/v1/assets/{id}/references	GET	List references
/v1/assets/folders	GET	List folders
/v1/assets/folders	POST	Create folder
/v1/assets/folders/{id}	PUT	Update folder
/v1/assets/folders/{id}	DELETE	Delete folder
/v1/assets/folders/{id}/contents	GET	List folder contents
/v1/assets/tags	GET	List tags
/v1/assets/tags	POST	Create tag
/v1/assets/tags/{id}	DELETE	Delete tag
/v1/assets/{id}/tags	POST	Add tags to asset
/v1/assets/{id}/tags	DELETE	Remove tags from asset
/v1/assets/search	POST	Search assets
/v1/assets/stats	GET	Usage statistics
Request structure for upload:

Field	Required	Description
file	Yes	Multipart file
name	No	Override filename
folder_id	No	Target folder
tags	No	Initial tags
description	No	Asset description
Response structure for asset:

Field	Description
asset_id	Unique identifier
name	Asset name
asset_type	Type category
file_size	Size in bytes
status	Processing status
metadata	Type-specific data
folder	Folder details
tags	Applied tags
versions_count	Number of versions
references_count	Usage count
urls	Access URLs
created_at	Upload timestamp
Testing requirements:

Test Category	Coverage
Upload	All file types, size limits
Validation	Invalid files, MIME mismatches
Metadata	Extraction accuracy
Folders	CRUD, nesting, limits
Tags	CRUD, bulk operations
Search	All filter combinations
Versions	Create, rollback, prune
References	Tracking, deletion protection
Isolation	Cross-user access prevention
Performance	Large file handling
Validation tests:

File type restrictions enforced
Size limits enforced
Metadata extraction accurate
Folder depth limits work
Tag uniqueness enforced
Search returns correct results
Versions maintain integrity
References prevent unwanted deletion
URLs expire correctly
Deliverables for Saturday:

All API endpoints implemented
Request and response validation
Comprehensive test suite
File handling edge cases
Documentation for asset library
Database Concepts Needed
Assets table:

asset_id UUID primary key
user_id foreign key
name not null
description text
asset_type enum not null
mime_type not null
file_extension not null
file_size integer not null
storage_path not null
original_filename not null
checksum not null
status enum not null
metadata JSONB
folder_id foreign key nullable
created_at timestamp
updated_at timestamp
Asset versions table:

version_id UUID primary key
asset_id foreign key
version_number integer not null
storage_path not null
file_size integer not null
checksum not null
metadata JSONB
change_description text
created_at timestamp
created_by foreign key
Folders table:

folder_id UUID primary key
user_id foreign key
parent_folder_id foreign key nullable
name not null
description text
color varchar
asset_count integer default 0
created_at timestamp
updated_at timestamp
Tags table:

tag_id UUID primary key
user_id foreign key
name not null
color varchar
usage_count integer default 0
created_at timestamp
Asset tags table:

asset_id foreign key
tag_id foreign key
primary key (asset_id, tag_id)
created_at timestamp
Asset references table:

reference_id UUID primary key
asset_id foreign key
resource_type not null
resource_id not null
usage_type not null
created_at timestamp
Indexes needed:

assets(user_id, status)
assets(user_id, asset_type)
assets(user_id, folder_id)
assets(checksum)
asset_versions(asset_id)
folders(user_id, parent_folder_id)
asset_tags(asset_id)
asset_tags(tag_id)
asset_references(asset_id)
asset_references(resource_type, resource_id)
Files To Create
File	Purpose
app/assets/models.py	Asset, Version, Folder, Tag models
app/assets/storage.py	File storage utilities
app/assets/upload.py	Upload processing pipeline
app/assets/metadata.py	Metadata extraction
app/assets/thumbnails.py	Preview generation
app/assets/versions.py	Version management
app/assets/folders.py	Folder operations
app/assets/tags.py	Tag operations
app/assets/search.py	Search functionality
app/assets/references.py	Reference tracking
app/assets/urls.py	URL generation
app/assets/service.py	Main asset service
app/api/asset_routes.py	API endpoints
tests/test_assets.py	Comprehensive tests
Success Criteria for Week 33
Creators can upload images, audio, video, fonts, and logos. Upload validation rejects invalid files. Metadata is extracted accurately for all types.

Folders enable hierarchical organization. Tags enable flexible categorization. Search finds assets by multiple criteria.

Versions track asset history. Rollback restores previous versions. Duplicate detection prevents waste.

References track where assets are used. Deletion protection prevents breaking references. Usage statistics show asset popularity.

URLs provide secure access to assets. Signed URLs expire correctly. Thumbnails load quickly.

Integration Points
With Project System:
Projects can reference assets for thumbnails, backgrounds, overlays.

With Template System (Week 25):
Templates can include default assets.

With Thumbnail Engine (Week 30):
Generated thumbnails can be saved as assets.

With Authentication (Week 32):
All assets are user-owned and isolated.

With Observability (Week 31):
Upload events and errors are logged.

What This Enables
After Week 33, creators have a personal media library. Brand assets are uploaded once and used everywhere. Logo consistency is automatic. Intro clips are reusable. Music tracks are organized and searchable.

This shifts the workflow from project-centric to creator-centric, enabling professional content production at scale.

