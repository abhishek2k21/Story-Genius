Week 34 Plan: Project Organization
Objective
Build project management system with folders, tagging, search, archiving, favorites, and bulk operations. After this week, creators can manage hundreds of projects efficiently with professional organizational tools.

Why This Week
Week 33 organized assets. Now projects need the same treatment. A creator producing 10 videos per week accumulates 500+ projects per year. Without organization, finding past work becomes impossible. Project organization transforms Story-Genius from a creation tool into a content management system.

Day-by-Day Breakdown
Monday: Project Folder System
Focus: Build hierarchical folder structure for organizing projects.

What to build:

Project folder model:

Field	Type	Purpose
folder_id	UUID	Unique identifier
user_id	UUID	Owner reference
parent_folder_id	UUID	Parent folder, nullable for root
name	string	Folder name
description	string	Optional description
color	string	UI color hint
icon	string	Optional icon identifier
project_count	integer	Cached project count
is_default	boolean	Default folder for new projects
sort_order	integer	Custom ordering
created_at	timestamp	Creation time
updated_at	timestamp	Last modification
Default folders created per user:

Folder	Purpose
Drafts	Work in progress
Published	Completed and posted
Archive	Old projects
Folder hierarchy rules:

Rule	Value	Reasoning
Maximum depth	4 levels	Prevent over-nesting
Maximum folders	100 per user	Resource limits
Name uniqueness	Within same parent	Avoid confusion
Name length	1-50 characters	UI constraints
Folder operations:

Operation	Description
Create	New folder in parent
Rename	Change folder name
Move	Change parent folder
Delete	Remove empty folder
Delete recursive	Remove folder and contents
Reorder	Change sort position
Set default	Mark as default for new projects
Project-folder relationship:

Behavior	Implementation
Assignment	Project has optional folder_id
Default	New projects go to default folder or root
Move	Update project folder_id
Bulk move	Move multiple projects
Folder deletion	Projects move to parent or root
Folder statistics:

Statistic	Calculation
project_count	Count of projects in folder
total_count	Including subfolders recursively
last_activity	Most recent project update
Deliverables for Monday:

Folder model and schema
Folder CRUD operations
Hierarchy validation
Project-folder relationship
Default folder creation
Folder statistics
Tuesday: Project Tagging and Metadata
Focus: Build tagging system and enhanced metadata for project categorization.

What to build:

Project tag model:

Field	Type	Purpose
tag_id	UUID	Unique identifier
user_id	UUID	Owner reference
name	string	Tag name
color	string	UI color
description	string	Optional description
usage_count	integer	Cached count
created_at	timestamp	Creation time
Tag categories (optional grouping):

Category	Example Tags
Content Type	educational, entertainment, tutorial
Platform	youtube, instagram, tiktok
Status	draft, review, published
Series	series-a, series-b
Client	client-x, client-y
Project metadata enhancements:

Field	Type	Purpose
folder_id	UUID	Folder assignment
tags	list	Applied tags
is_favorite	boolean	Starred project
is_archived	boolean	Archived status
color	string	Visual identifier
notes	text	Creator notes
external_url	string	Published URL
published_at	timestamp	When published
performance_data	JSON	Views, likes, etc.
Tag operations:

Operation	Description
Create tag	New tag for user
Update tag	Change name, color
Delete tag	Remove tag, unlink from projects
Merge tags	Combine two tags into one
Apply to project	Link tag to project
Remove from project	Unlink tag
Bulk apply	Add tag to multiple projects
Bulk remove	Remove tag from multiple projects
Auto-tagging suggestions:

Trigger	Suggested Tags
Platform selected	Platform tag
Template used	Template-based tag
Content category	Category tag
Batch membership	Batch tag
Tag limits:

Limit	Value
Tags per project	20 maximum
Tags per user	200 maximum
Tag name length	1-30 characters
Deliverables for Tuesday:

Tag model and schema
Tag CRUD operations
Project-tag relationship
Bulk tagging operations
Tag merge functionality
Auto-tag suggestions
Wednesday: Project Search and Filtering
Focus: Build comprehensive search system for finding projects by multiple criteria.

What to build:

Search criteria:

Criterion	Type	Description
query	string	Text search in name, description
folder_id	UUID	Filter by folder
folder_recursive	boolean	Include subfolders
tags	list	Filter by tags (AND/OR)
tag_match	enum	all, any
status	enum	draft, processing, completed, failed
is_favorite	boolean	Starred only
is_archived	boolean	Archived status
platform	enum	Target platform
template_id	UUID	Created from template
batch_id	UUID	Part of batch
created_after	timestamp	Creation date range
created_before	timestamp	Creation date range
updated_after	timestamp	Update date range
updated_before	timestamp	Update date range
has_output	boolean	Has generated video
duration_min	integer	Minimum duration
duration_max	integer	Maximum duration
Search response:

Field	Description
results	Paginated project list
total_count	Total matching projects
page	Current page
page_size	Results per page
facets	Aggregation counts
Facet aggregations:

Facet	Purpose
by_status	Count per status
by_platform	Count per platform
by_folder	Count per folder
by_tag	Count per tag
by_month	Count per creation month
Sort options:

Sort	Description
created_desc	Newest first
created_asc	Oldest first
updated_desc	Recently modified
updated_asc	Least recently modified
name_asc	Alphabetical A-Z
name_desc	Alphabetical Z-A
duration_asc	Shortest first
duration_desc	Longest first
Saved searches:

Field	Purpose
search_id	Unique identifier
user_id	Owner
name	Search name
criteria	Saved search criteria
is_default	Default view
Deliverables for Wednesday:

Search service with all criteria
Facet aggregation
Sort implementation
Pagination
Saved search CRUD
Search performance optimization
Thursday: Archive and Favorites System
Focus: Build archiving workflow and favorites for quick access.

What to build:

Archive behavior:

Aspect	Implementation
Visibility	Archived projects hidden from default views
Access	Still accessible via search and direct link
Restoration	Can unarchive anytime
Storage	Same as regular projects
Bulk archive	Archive multiple projects
Archive workflow:

Action	Result
Archive project	Set is_archived true, move to Archive folder
Unarchive project	Set is_archived false, move to original folder
Bulk archive	Archive multiple, move all to Archive
Auto-archive	Optional rule-based archiving
Auto-archive rules (optional):

Rule	Trigger
Age-based	Projects older than X days
Status-based	Completed projects after X days
Inactivity	No updates for X days
Favorites system:

Feature	Implementation
Mark favorite	Set is_favorite true
Unmark favorite	Set is_favorite false
Favorites view	Quick filter for favorites
Favorites limit	None
Favorites sort	Can sort by favorited date
Quick access features:

Feature	Purpose
Recent projects	Last 10 accessed
Favorites	Starred projects
Pinned folders	Quick folder access
Saved searches	Frequent filters
Recent projects tracking:

Field	Purpose
project_id	Referenced project
user_id	User
accessed_at	Access timestamp
Track last 50 accesses, deduplicated by project.

Deliverables for Thursday:

Archive flag and operations
Bulk archive functionality
Favorites flag and operations
Recent projects tracking
Quick access queries
Auto-archive rules engine
Friday: Bulk Operations and Project Actions
Focus: Build bulk operations for efficient project management at scale.

What to build:

Bulk selection:

Method	Description
Individual	Select specific projects
All in view	Select all visible projects
All matching	Select all search results
Range	Select range by shift-click logic
Bulk operations:

Operation	Description
Move to folder	Move all selected to folder
Add tags	Apply tags to all selected
Remove tags	Remove tags from all selected
Archive	Archive all selected
Unarchive	Unarchive all selected
Delete	Delete all selected
Duplicate	Create copies of all selected
Export	Export project data
Change status	Update status for all
Bulk operation processing:

Aspect	Implementation
Limit	Maximum 100 projects per operation
Validation	Validate all before processing
Transaction	All or nothing for data integrity
Progress	Track completion percentage
Errors	Collect and report individual failures
Bulk operation response:

Field	Description
operation_id	Unique identifier
total_count	Projects in operation
success_count	Successfully processed
failure_count	Failed to process
failures	List of failures with reasons
Project duplication:

Aspect	Behavior
Name	Original name + " (copy)"
Folder	Same as original
Tags	Copied from original
Configuration	Copied from original
Outputs	Not copied
Status	Reset to draft
Project deletion:

Type	Behavior
Soft delete	Set deleted_at, hide from views
Hard delete	Permanent removal after retention
Retention	30 days for soft deleted
Restore	Undelete within retention period
Trash system:

Feature	Implementation
Trash view	List soft-deleted projects
Restore	Undelete from trash
Empty trash	Permanent delete all
Auto-empty	After 30 days
Deliverables for Friday:

Bulk selection logic
All bulk operations
Operation validation
Progress tracking
Duplication service
Soft delete and trash
Restore functionality
Saturday: API Endpoints and Testing
Focus: Expose project organization capabilities via API and comprehensive testing.

What to build:

API endpoints:

Endpoint	Method	Description
/v1/projects	GET	List projects with filters
/v1/projects/search	POST	Advanced search
/v1/projects/recent	GET	Recent projects
/v1/projects/favorites	GET	Favorite projects
/v1/projects/trash	GET	Deleted projects
/v1/projects/{id}	GET	Get project details
/v1/projects/{id}	PUT	Update project
/v1/projects/{id}	DELETE	Delete project
/v1/projects/{id}/restore	POST	Restore from trash
/v1/projects/{id}/duplicate	POST	Duplicate project
/v1/projects/{id}/favorite	POST	Mark favorite
/v1/projects/{id}/unfavorite	POST	Unmark favorite
/v1/projects/{id}/archive	POST	Archive project
/v1/projects/{id}/unarchive	POST	Unarchive project
/v1/projects/{id}/move	POST	Move to folder
/v1/projects/{id}/tags	POST	Add tags
/v1/projects/{id}/tags	DELETE	Remove tags
/v1/projects/bulk/move	POST	Bulk move
/v1/projects/bulk/tag	POST	Bulk tag
/v1/projects/bulk/archive	POST	Bulk archive
/v1/projects/bulk/delete	POST	Bulk delete
/v1/projects/bulk/duplicate	POST	Bulk duplicate
/v1/projects/folders	GET	List folders
/v1/projects/folders	POST	Create folder
/v1/projects/folders/{id}	GET	Get folder
/v1/projects/folders/{id}	PUT	Update folder
/v1/projects/folders/{id}	DELETE	Delete folder
/v1/projects/folders/{id}/contents	GET	Folder contents
/v1/projects/tags	GET	List tags
/v1/projects/tags	POST	Create tag
/v1/projects/tags/{id}	PUT	Update tag
/v1/projects/tags/{id}	DELETE	Delete tag
/v1/projects/tags/{id}/merge	POST	Merge tags
/v1/projects/searches	GET	List saved searches
/v1/projects/searches	POST	Save search
/v1/projects/searches/{id}	DELETE	Delete saved search
Request structure for search:

Field	Required	Description
query	No	Text search
folder_id	No	Folder filter
tags	No	Tag filter
tag_match	No	all or any
status	No	Status filter
is_favorite	No	Favorites only
is_archived	No	Include archived
platform	No	Platform filter
created_after	No	Date range start
created_before	No	Date range end
sort	No	Sort field
sort_direction	No	asc or desc
page	No	Page number
page_size	No	Results per page
include_facets	No	Return facets
Response structure for search:

Field	Description
results	Project list
total_count	Total matches
page	Current page
page_size	Page size
total_pages	Total pages
facets	Aggregation counts
Request structure for bulk operations:

Field	Required	Description
project_ids	Yes	List of project IDs
folder_id	For move	Target folder
tags	For tag	Tags to apply
remove_tags	For untag	Tags to remove
Testing requirements:

Test Category	Coverage
Folders	CRUD, hierarchy, limits
Tags	CRUD, merge, limits
Search	All criteria, facets, sorting
Archive	Archive, unarchive, visibility
Favorites	Mark, unmark, filtering
Bulk ops	All operations, limits, errors
Trash	Delete, restore, auto-empty
Isolation	Cross-user prevention
Performance	Search with many projects
Validation tests:

Folder depth limits enforced
Tag limits enforced
Bulk operation limits work
Search returns accurate results
Facets calculate correctly
Archive hides from default views
Trash retention works
Restore recovers correctly
Deliverables for Saturday:

All API endpoints implemented
Request and response validation
Comprehensive test suite
Bulk operation error handling
Documentation for project organization
Database Concepts Needed
Project folders table:

folder_id UUID primary key
user_id foreign key
parent_folder_id foreign key nullable
name not null
description text
color varchar
icon varchar
project_count integer default 0
is_default boolean default false
sort_order integer default 0
created_at timestamp
updated_at timestamp
Project tags table:

tag_id UUID primary key
user_id foreign key
name not null
color varchar
description text
usage_count integer default 0
created_at timestamp
Project tag assignments table:

project_id foreign key
tag_id foreign key
primary key (project_id, tag_id)
created_at timestamp
Saved searches table:

search_id UUID primary key
user_id foreign key
name not null
criteria JSONB not null
is_default boolean default false
created_at timestamp
updated_at timestamp
Recent projects table:

id UUID primary key
user_id foreign key
project_id foreign key
accessed_at timestamp
Update projects table:

Add folder_id foreign key nullable
Add is_favorite boolean default false
Add is_archived boolean default false
Add color varchar
Add notes text
Add external_url varchar
Add published_at timestamp
Add deleted_at timestamp nullable
Add performance_data JSONB
Indexes needed:

project_folders(user_id, parent_folder_id)
project_tags(user_id)
project_tag_assignments(project_id)
project_tag_assignments(tag_id)
projects(user_id, folder_id)
projects(user_id, is_favorite)
projects(user_id, is_archived)
projects(user_id, deleted_at)
projects(user_id, created_at)
recent_projects(user_id, accessed_at)
saved_searches(user_id)
Files To Create
File	Purpose
app/projects/folders.py	Folder operations
app/projects/tags.py	Tag operations
app/projects/search.py	Search service
app/projects/archive.py	Archive operations
app/projects/favorites.py	Favorites operations
app/projects/bulk.py	Bulk operations
app/projects/trash.py	Trash and restore
app/projects/recent.py	Recent projects tracking
app/projects/organization.py	Main organization service
app/api/project_org_routes.py	API endpoints
tests/test_project_organization.py	Comprehensive tests
Success Criteria for Week 34
Creators can organize projects into hierarchical folders up to 4 levels deep. Tags provide flexible cross-folder categorization. Search finds projects by any combination of criteria.

Favorites provide quick access to important projects. Archive removes old projects from default views while preserving access. Trash enables recovery of deleted projects.

Bulk operations work on up to 100 projects efficiently. All operations validate before processing. Errors are collected and reported clearly.

Recent projects track access history. Saved searches preserve frequent filters. Project organization scales to hundreds of projects per creator.

Integration Points
With Asset Library (Week 33):
Projects reference assets, asset references remain valid during project moves.

With Template System (Week 25):
Templates can specify default folder for projects created from them.

With Batch System (Week 24):
Batch projects can be organized together, bulk operations work on batch outputs.

With Authentication (Week 32):
All organization is user-scoped and isolated.

With Observability (Week 31):
Organization operations are logged, search performance is tracked.

What This Enables
After Week 34, creators can manage professional content libraries. Projects for different clients go in different folders. Series content is tagged together. Old projects are archived but accessible. Finding past work takes seconds.

This transforms Story-Genius from a content creation tool into a content management platform.