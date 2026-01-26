Week 26 Plan: Recovery and Reliability
Objective
Harden the system for production use by implementing job checkpointing, automatic retry logic, state recovery after failures, and cleanup routines. After this week, the system can survive crashes, resume interrupted work, and maintain data integrity under failure conditions.

Why This Week
You have built a capable system that works when everything goes right. Production systems fail. Servers restart. Processes crash. Network calls timeout. Database connections drop. Without recovery mechanisms, a single failure can corrupt batch state, lose creator work, and require manual intervention.

Reliability is not a feature. It is the foundation that makes all other features trustworthy.

What To Build
Job Checkpointing System
Problem it solves: Currently if a job fails mid-pipeline, all progress is lost. Creator must restart from beginning.

What checkpointing does:

Saves job state at each stage boundary
Records completed stages with their outputs
Stores pending stages with their inputs
Enables resumption from last successful checkpoint
Checkpoint data structure:

Job identifier
Current stage identifier
Stage status indicating completed, in-progress, or pending
Stage input reference
Stage output reference if completed
Timestamp of checkpoint
Retry count for current stage
Checkpoint triggers:

Before starting each stage
After completing each stage
On any stage failure
On graceful shutdown signal
Checkpoint storage:

Database table for durability
Not in-memory or file-based
Queryable for recovery operations
Automatic Retry Logic
Problem it solves: Transient failures like network timeouts, temporary API errors, and resource contention currently cause permanent job failure.

Retry strategy:

Exponential backoff starting at 1 second
Maximum 5 retry attempts per stage
Jitter added to prevent thundering herd
Different retry limits for different failure types
Failure classification:

Failure Type	Retry Behavior
Network timeout	Retry with backoff
API rate limit	Retry with longer backoff
Resource unavailable	Retry with backoff
Invalid input	No retry, permanent failure
Authentication failure	No retry, permanent failure
Out of memory	Retry once after cleanup
Unknown error	Retry with backoff, escalate after max
Retry state tracking:

Attempt count per stage
Last failure reason
Last failure timestamp
Next retry scheduled time
Dead Letter Handling
Problem it solves: Jobs that fail permanently need proper handling. Currently they may sit in limbo or disappear.

Dead letter queue concept:

Jobs that exhaust retry attempts move to dead letter state
Dead letter jobs are preserved with full failure context
Dead letter jobs can be manually reviewed
Dead letter jobs can be manually retried after fixes
Dead letter jobs can be permanently dismissed
Dead letter record contains:

Original job with all configuration
All checkpoint history
All failure attempts with reasons
Stage where permanent failure occurred
Timestamp of final failure
Resolution status indicating pending review, retried, or dismissed
Dead letter operations:

List dead letter jobs with filtering
Get full failure context for a job
Retry dead letter job from last checkpoint
Retry dead letter job from beginning
Dismiss dead letter job permanently
State Recovery After Restart
Problem it solves: If the server restarts, in-progress jobs are abandoned. Batches may show as processing forever.

Recovery on startup:

Scan for jobs in processing state
Check last checkpoint for each job
Determine if job can be resumed
Queue resumable jobs for continuation
Move non-resumable jobs to dead letter
Recovery decision logic:

If checkpoint exists and is valid, resume from checkpoint
If checkpoint is corrupted, move to dead letter with context
If no checkpoint but job just started, restart from beginning
If job was in final export stage, verify output and complete or retry
Batch recovery:

Batches in processing state are scanned
Individual items are recovered per rules above
Batch status is recalculated from item statuses
Batch progress is updated accurately
Recovery timing:

Automatic on application startup
Can be triggered manually via admin endpoint
Runs before accepting new jobs
Graceful Shutdown Handling
Problem it solves: Hard shutdown interrupts jobs at arbitrary points, potentially corrupting state.

Graceful shutdown sequence:

Stop accepting new jobs
Signal in-progress jobs to checkpoint
Wait for current stage to complete or timeout
Save final checkpoint for all active jobs
Mark jobs as interrupted with resume capability
Close database connections cleanly
Exit process
Shutdown timeout:

Maximum wait time for in-progress stages
After timeout, force checkpoint and exit
Configurable based on longest expected stage duration
Shutdown signals handled:

SIGTERM for container orchestration
SIGINT for manual shutdown
Application-level shutdown request
Artifact Cleanup Routines
Problem it solves: Failed jobs leave behind partial artifacts. Storage grows indefinitely. Orphaned files accumulate.

Cleanup targets:

Artifacts from failed jobs that will not be retried
Temporary files from in-progress stages
Preview files older than retention period
Completed job artifacts past retention period
Orphaned files with no database reference
Cleanup rules:

Artifact Type	Retention	Cleanup Trigger
Failed job artifacts	7 days	Daily cleanup job
Dead letter artifacts	30 days	Weekly cleanup job
Preview files	24 hours	Hourly cleanup job
Successful outputs	User-defined	On user deletion or expiry
Temporary stage files	1 hour	Continuous cleanup
Orphaned files	Immediate	Daily orphan scan
Cleanup safety:

Never delete artifacts for in-progress jobs
Never delete artifacts for jobs pending retry
Verify no references before deletion
Log all deletions for audit
Cleanup operations:

Automatic scheduled cleanup
Manual cleanup trigger via admin endpoint
Dry-run mode to preview what would be deleted
Cleanup statistics reporting
Health Check System
Problem it solves: Cannot determine if system is functioning correctly. No visibility into internal state.

Health check components:

Component	Check Method
Database connectivity	Execute simple query
Job queue status	Count pending, processing, failed
Storage availability	Check disk space and write access
External API dependencies	Ping with timeout
Memory usage	Check against threshold
Processing throughput	Compare to baseline
Health check endpoints:

Liveness check for container orchestration
Readiness check for load balancer
Deep health check for diagnostics
Health check responses:

Healthy with all components operational
Degraded with some components impaired
Unhealthy with critical components failed
Basic Observability Hooks
Problem it solves: Cannot debug issues without visibility into system behavior.

Structured logging requirements:

Every job state transition logged
Every checkpoint logged
Every retry attempt logged with reason
Every failure logged with context
Every cleanup action logged
Log format:

Timestamp in ISO format
Log level
Component identifier
Job identifier if applicable
Batch identifier if applicable
Event type
Event details as structured data
Key events to log:

Job created
Stage started
Stage completed
Stage failed with reason
Checkpoint saved
Retry scheduled
Retry attempted
Dead letter queued
Recovery initiated
Cleanup performed
Metrics to track:

Jobs created per hour
Jobs completed per hour
Jobs failed per hour
Average job duration
Average stage duration
Retry rate per stage
Dead letter rate
Recovery success rate
Cleanup volume
Database Concepts Needed
Job checkpoint table:

Job reference
Stage identifier
Stage status
Input artifact reference
Output artifact reference
Checkpoint timestamp
Retry count
Last error message
Dead letter table:

Original job snapshot
Failure stage
Failure reason
All retry attempts as structured data
Final failure timestamp
Resolution status
Resolution timestamp
Resolution notes
Cleanup tracking table:

Cleanup run timestamp
Cleanup type
Items scanned
Items deleted
Bytes reclaimed
Errors encountered
Health status table:

Component identifier
Last check timestamp
Status
Details
How To Think About It
Reliability is about making failure a normal part of operations, not an exceptional crisis. The system should expect failures and handle them automatically. Creator should never know that a retry happened. Creator should never lose work due to infrastructure issues.

The goal is not zero failures. The goal is zero data loss and minimal manual intervention.

Backend Capabilities Required
Checkpoint Operations
Create checkpoint for job and stage
Get latest checkpoint for job
Get all checkpoints for job
Delete checkpoints for completed job
Validate checkpoint integrity
Retry Operations
Schedule retry for failed stage
Execute retry with backoff calculation
Record retry attempt
Escalate to dead letter after max retries
Dead Letter Operations
Move job to dead letter with context
List dead letter jobs with filters
Get dead letter job details
Retry from dead letter
Dismiss from dead letter
Recovery Operations
Scan for interrupted jobs
Recover job from checkpoint
Recover batch from item states
Report recovery results
Cleanup Operations
Run cleanup for artifact type
Scan for orphaned artifacts
Delete artifacts safely
Report cleanup results
Health Operations
Check individual component
Check all components
Get health summary
Get health history
Validation Rules
Checkpoint validation:

Checkpoint must reference valid job
Checkpoint stage must be valid for job type
Checkpoint artifacts must exist if referenced
Checkpoint timestamp must be logical
Retry validation:

Retry count must not exceed maximum
Failure type must be retryable
Backoff time must have elapsed
Job must not be cancelled
Dead letter validation:

Job must have exhausted retries or be non-retryable
Full context must be preserved
Job must not already be in dead letter
Cleanup validation:

Artifact must not be referenced by active job
Artifact must exceed retention period
Cleanup must be logged before execution
Success Criteria for Week 26
Server can restart and automatically resume all interrupted jobs from their last checkpoint. Transient failures trigger automatic retry with exponential backoff. Permanent failures move to dead letter queue with full context for manual review. Dead letter jobs can be retried or dismissed through API.

Graceful shutdown saves state for all in-progress jobs. Cleanup routines prevent storage growth from failed jobs. Health checks accurately report system status. Structured logs provide visibility into all reliability operations.

Creator never loses work due to system failure. Creator is not aware of automatic retries. System recovers from crashes without manual intervention.

Files To Create
File	Purpose
app/reliability/checkpointing.py	Checkpoint save, load, validate
app/reliability/retry.py	Retry logic with backoff
app/reliability/dead_letter.py	Dead letter queue management
app/reliability/recovery.py	Startup recovery procedures
app/reliability/shutdown.py	Graceful shutdown handling
app/reliability/cleanup.py	Artifact cleanup routines
app/reliability/health.py	Health check system
app/api/admin_routes.py	Admin endpoints for reliability operations
API Endpoints To Implement
Endpoint	Method	Description
/v1/admin/health	GET	Full health check
/v1/admin/health/live	GET	Liveness probe
/v1/admin/health/ready	GET	Readiness probe
/v1/admin/dead-letter	GET	List dead letter jobs
/v1/admin/dead-letter/{id}	GET	Get dead letter details
/v1/admin/dead-letter/{id}/retry	POST	Retry from dead letter
/v1/admin/dead-letter/{id}/dismiss	POST	Dismiss from dead letter
/v1/admin/recovery/scan	POST	Trigger recovery scan
/v1/admin/cleanup/run	POST	Trigger cleanup
/v1/admin/cleanup/preview	GET	Preview cleanup targets
/v1/admin/jobs/{id}/checkpoints	GET	Get job checkpoints
Integration Points
With Stage Pipeline:
Checkpoints align with stage boundaries. Each stage completion is a checkpoint opportunity.

With Batch System:
Batch recovery aggregates item recovery. Batch status recalculates from recovered item states.

With Template System:
Template instantiation creates checkpointable jobs. Template references are preserved through recovery.

With Quality Validation:
Quality failures may be retryable or permanent depending on failure type.

What This Enables
After Week 26, Story-Genius becomes a system that creators can trust with real production workloads. Jobs complete reliably. Failures are handled automatically. Crashes do not lose work. Storage does not grow unbounded. Operators have visibility into system health.

This is the threshold between a prototype and a product.