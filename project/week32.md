Week 32 Plan: Authentication and User Isolation
Objective
Build user management system with API key authentication, project ownership, resource isolation, and permission validation. After this week, multiple creators can use the system securely with completely isolated resources.

Why This Week
Everything built so far is single-user. One creator uses the system. Adding a second creator would expose their work to each other. API endpoints are open to anyone. This is not deployable. Authentication transforms Story-Genius from a local tool into a multi-tenant platform.

Day-by-Day Breakdown
Monday: User Management Foundation
Focus: Build user model and core user management operations.

What to build:

User model structure:

Field	Type	Purpose
user_id	UUID	Unique identifier
email	string	Login identifier, unique
username	string	Display name, unique
password_hash	string	Secured password
status	enum	active, suspended, deleted
role	enum	creator, admin
created_at	timestamp	Registration time
updated_at	timestamp	Last modification
last_login_at	timestamp	Last successful login
email_verified	boolean	Email confirmation status
metadata	JSON	Additional user data
User status definitions:

Status	Meaning	Can Authenticate
active	Normal user	Yes
suspended	Temporarily disabled	No
deleted	Soft deleted	No
User role definitions:

Role	Permissions
creator	Own resources only
admin	All resources, system management
Password security requirements:

Requirement	Value
Minimum length	8 characters
Hashing algorithm	bcrypt
Salt rounds	12
Password history	Last 3 passwords
User management operations:

Operation	Description
Create user	Register new user
Get user	Retrieve user details
Update user	Modify user fields
Delete user	Soft delete user
List users	Admin only, paginated
Suspend user	Admin only
Activate user	Admin only
Change password	Requires current password
Reset password	Email-based flow
Deliverables for Monday:

User model and database schema
Password hashing utilities
User CRUD service
User validation rules
Admin user seeding
Tuesday: API Key System
Focus: Build API key generation, validation, and management.

What to build:

API key model structure:

Field	Type	Purpose
key_id	UUID	Unique identifier
user_id	UUID	Owner reference
key_hash	string	Hashed key value
key_prefix	string	First 8 chars for identification
name	string	User-defined label
status	enum	active, revoked, expired
permissions	list	Allowed operations
rate_limit	integer	Requests per minute
created_at	timestamp	Creation time
expires_at	timestamp	Expiration time, optional
last_used_at	timestamp	Last successful use
usage_count	integer	Total uses
API key format:

sg_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Part	Purpose
sg	Product prefix
live/test	Environment indicator
32 chars	Random secure token
API key security:

Measure	Implementation
Storage	Hash only, never store raw
Display	Show full key only once at creation
Rotation	Old key works for grace period
Revocation	Immediate effect
API key operations:

Operation	Description
Create key	Generate new key, return raw value once
List keys	User's keys, masked values
Get key	Key details, masked value
Revoke key	Immediately disable
Rotate key	Create new, grace period for old
Update key	Change name, permissions, rate limit
Key permission scopes:

Scope	Allows
read	GET operations only
write	All CRUD operations
batch	Batch operations
admin	Administrative operations
Deliverables for Tuesday:

API key model and schema
Key generation utilities
Key hashing and validation
Key CRUD service
Key permission definitions
Wednesday: Authentication Middleware
Focus: Build authentication middleware that validates requests and sets user context.

What to build:

Authentication methods:

Method	Use Case	Header
API Key	Programmatic access	X-API-Key
Bearer Token	Session-based access	Authorization
Authentication flow:

Request arrives at API
Middleware extracts credentials
Credentials are validated
User and permissions are loaded
Request context is set with user info
Request proceeds to handler
If validation fails, return 401
Middleware responsibilities:

Responsibility	Implementation
Extract credentials	Parse headers
Validate format	Check credential structure
Verify credentials	Check against database
Check status	Ensure user/key is active
Check permissions	Verify scope for endpoint
Set context	Add user to request state
Log authentication	Record success/failure
Authentication response codes:

Code	Meaning	When Used
401	Unauthorized	Missing or invalid credentials
403	Forbidden	Valid credentials, insufficient permissions
Error response structure:

Field	Type	Purpose
error	string	Error type
message	string	Human-readable message
code	string	Machine-readable code
Rate limiting integration:

Check rate limit from API key
Track usage in sliding window
Return 429 if exceeded
Include retry-after header
Deliverables for Wednesday:

Authentication middleware
Credential extraction utilities
Validation logic
Context setting
Rate limiting checks
Error response formatting
Thursday: Resource Ownership and Isolation
Focus: Build ownership model and ensure complete resource isolation between users.

What to build:

Owned resource types:

Resource	Ownership Field
Project	user_id
Job	user_id
Batch	user_id
Template	user_id
Asset	user_id
API Key	user_id
Ownership enforcement:

Operation	Check
Create	Set user_id from context
Read	Verify user_id matches context
Update	Verify user_id matches context
Delete	Verify user_id matches context
List	Filter by user_id from context
Database query modification:

All queries automatically include user_id filter:

SELECT adds WHERE user_id = current_user
UPDATE adds WHERE user_id = current_user
DELETE adds WHERE user_id = current_user
Shared resources:

Resource	Sharing Model
System templates	Available to all, owned by system
Style presets	System presets public, user presets private
Hook templates	System templates public
Admin override:

Admin users can:

Read any resource
Modify any resource
Access cross-user statistics
Perform system operations
Isolation testing:

Test	Verification
User A cannot read User B project	404 returned
User A cannot update User B job	404 returned
User A list shows only own resources	Count matches
Admin can read all resources	Success
Deliverables for Thursday:

Ownership mixin for models
Query filter utilities
Ownership validation decorators
Admin override logic
Isolation test suite
Friday: Permission System and Validation
Focus: Build granular permission system and validation throughout the API.

What to build:

Permission model:

Permission	Description
projects:read	Read project details
projects:write	Create, update projects
projects:delete	Delete projects
jobs:read	Read job status
jobs:write	Create, cancel jobs
batches:read	Read batch details
batches:write	Create, manage batches
templates:read	Read templates
templates:write	Create, update templates
assets:read	Read assets
assets:write	Upload, manage assets
admin:users	Manage users
admin:system	System operations
Permission groupings:

Group	Permissions Included
readonly	All :read permissions
standard	All :read and :write permissions
full	All permissions except admin
admin	All permissions
Permission validation flow:

Request authenticated
Required permission determined from endpoint
User permissions loaded from role and API key
Check if required permission present
If missing, return 403
If present, proceed
Endpoint permission mapping:

Endpoint Pattern	Required Permission
GET /projects/*	projects:read
POST /projects	projects:write
DELETE /projects/*	projects:delete
GET /jobs/*	jobs:read
POST /jobs/*/cancel	jobs:write
GET /admin/*	admin:*
Permission inheritance:

Role provides base permissions
API key can restrict (not expand) role permissions
Admin role has all permissions
Creator role has standard permissions
Deliverables for Friday:

Permission definitions
Permission validation decorator
Endpoint permission mapping
Role permission assignments
API key permission restrictions
Saturday: API Endpoints and Testing
Focus: Expose authentication capabilities via API and comprehensive testing.

What to build:

API endpoints:

Endpoint	Method	Description
/v1/auth/register	POST	Create new user
/v1/auth/login	POST	Get session token
/v1/auth/logout	POST	Invalidate session
/v1/auth/refresh	POST	Refresh session token
/v1/auth/password/change	POST	Change password
/v1/auth/password/reset	POST	Request password reset
/v1/users/me	GET	Get current user
/v1/users/me	PUT	Update current user
/v1/users/me/keys	GET	List API keys
/v1/users/me/keys	POST	Create API key
/v1/users/me/keys/{id}	GET	Get API key details
/v1/users/me/keys/{id}	DELETE	Revoke API key
/v1/users/me/keys/{id}/rotate	POST	Rotate API key
/v1/admin/users	GET	List all users
/v1/admin/users/{id}	GET	Get user details
/v1/admin/users/{id}	PUT	Update user
/v1/admin/users/{id}/suspend	POST	Suspend user
/v1/admin/users/{id}/activate	POST	Activate user
Request structure for registration:

Field	Required	Description
email	Yes	User email
username	Yes	Display name
password	Yes	User password
Response structure for login:

Field	Description
access_token	JWT for API access
refresh_token	Token for refresh
expires_in	Seconds until expiration
user	User details
Response structure for API key creation:

Field	Description
key_id	Key identifier
key	Full key value (shown once)
name	Key name
permissions	Assigned permissions
created_at	Creation timestamp
Testing requirements:

Test Category	Coverage
Registration	Valid, duplicate, invalid inputs
Login	Correct, incorrect credentials
API key	Create, validate, revoke
Authentication	Valid, expired, revoked credentials
Authorization	Correct, insufficient permissions
Isolation	Cross-user access attempts
Rate limiting	Under and over limit
Admin operations	User management
Edge cases	Expired tokens, deleted users
Validation tests:

Passwords are properly hashed
API keys are not stored raw
Tokens expire correctly
Revocation is immediate
Isolation is complete
Permissions are enforced
Rate limits work correctly
Deliverables for Saturday:

All API endpoints implemented
Request and response validation
Comprehensive test suite
Security test coverage
Documentation for authentication
Database Concepts Needed
Users table:

user_id UUID primary key
email unique not null
username unique not null
password_hash not null
status enum not null
role enum not null
email_verified boolean
created_at timestamp
updated_at timestamp
last_login_at timestamp
metadata JSONB
API keys table:

key_id UUID primary key
user_id foreign key
key_hash not null
key_prefix not null
name not null
status enum not null
permissions JSONB
rate_limit integer
created_at timestamp
expires_at timestamp
last_used_at timestamp
usage_count integer
Sessions table (optional for token auth):

session_id UUID primary key
user_id foreign key
token_hash not null
created_at timestamp
expires_at timestamp
revoked_at timestamp
Password history table:

history_id UUID primary key
user_id foreign key
password_hash not null
created_at timestamp
Update existing tables:

Add user_id column to:

projects
jobs
batches
templates
All resource tables
Add foreign key constraint to users table.

Add index on user_id for all resource tables.

Files To Create
File	Purpose
app/auth/models.py	User, APIKey, Session models
app/auth/password.py	Password hashing utilities
app/auth/tokens.py	JWT token utilities
app/auth/keys.py	API key generation and validation
app/auth/service.py	Authentication service
app/auth/permissions.py	Permission definitions and checks
app/middleware/auth_middleware.py	Authentication middleware
app/middleware/ownership_middleware.py	Resource ownership checks
app/api/auth_routes.py	Authentication endpoints
app/api/user_routes.py	User management endpoints
tests/test_auth.py	Authentication tests
tests/test_isolation.py	Resource isolation tests
Success Criteria for Week 32
Users can register with email and password. Users can login and receive access token. Users can create and manage API keys.

API key authentication works for all endpoints. Bearer token authentication works for session-based access. Invalid credentials return 401.

Each user's resources are completely isolated. User A cannot access User B resources. Admin can access all resources.

Permissions are enforced on all endpoints. Insufficient permissions return 403. API keys can have restricted scopes.

Rate limiting prevents abuse. Password security meets requirements. Tokens expire and can be revoked.

Integration Points
With Observability (Week 31):
Authentication events are logged. Failed attempts are tracked. User context is included in all logs.

With All Resource Systems:
All existing resources gain user_id ownership. All queries filter by current user.

With Batch System (Week 24):
Batches are owned by users. Batch statistics are per-user.

With Template System (Week 25):
Templates are owned by users. System templates are shared.

What This Enables
After Week 32, Story-Genius becomes multi-tenant. Multiple creators can use the same system with complete isolation. API access is secured and trackable. The system is deployable for real-world usage.

This is the transition from development tool to production platform.

Migration Considerations
Existing data needs migration:

Create default admin user
Assign existing resources to admin or migrate
Add user_id to all existing records
Generate initial API keys
Migration must be planned before deployment.