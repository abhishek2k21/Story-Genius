"""
Collaboration API Routes
Endpoints for teams, comments, templates, scheduling, and integrations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.collaboration import team_manager, TeamRole, commenting_system
from app.templates import template_manager, TemplateVisibility
from app.scheduling import content_calendar
from app.integrations import youtube_integration, social_media_integration, webhook_manager, IntegrationType
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# Request Models

class CreateTeamRequest(BaseModel):
    name: str
    owner_id: str


class AddMemberRequest(BaseModel):
    user_id: str
    role: str  # owner, admin, editor, viewer


class UpdateRoleRequest(BaseModel):
    role: str


class AddCommentRequest(BaseModel):
    user_id: str
    target_id: str
    target_type: str  # video, project
    content: str
    timestamp: Optional[float] = None
    parent_id: Optional[str] = None


class CreateTemplateRequest(BaseModel):
    name: str
    description: str
    parameters: dict
    visibility: str  # personal, team, public
    team_id: Optional[str] = None
    tags: Optional[List[str]] = None


class ScheduleVideoRequest(BaseModel):
    video_id: str
    publish_date: str  # ISO format
    platforms: Optional[List[str]] = None


class CreateSeriesRequest(BaseModel):
    name: str
    frequency: str  # daily, weekly, monthly
    videos: List[str]


# TEAM MANAGEMENT ROUTES

@router.post("/teams")
async def create_team(request: CreateTeamRequest):
    """Create a new team"""
    try:
        import uuid
        team_id = str(uuid.uuid4())
        
        team = team_manager.create_team(
            team_id=team_id,
            name=request.name,
            owner_id=request.owner_id
        )
        
        return {
            "team_id": team.team_id,
            "name": team.name,
            "owner_id": team.owner_id,
            "created_at": team.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    """Get team details"""
    try:
        team = team_manager.get_team(team_id)
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        members = [
            {
                "user_id": m.user_id,
                "role": m.role.value,
                "joined_at": m.joined_at.isoformat()
            }
            for m in team.members.values()
        ]
        
        return {
            "team_id": team.team_id,
            "name": team.name,
            "owner_id": team.owner_id,
            "members": members,
            "created_at": team.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/members")
async def add_team_member(team_id: str, request: AddMemberRequest, invited_by: str):
    """Add member to team"""
    try:
        role = TeamRole(request.role)
        
        team_manager.add_member(
            team_id=team_id,
            user_id=request.user_id,
            role=role,
            invited_by=invited_by
        )
        
        return {"status": "success", "message": f"Added {request.user_id} to team"}
    except Exception as e:
        logger.error(f"Failed to add member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/activity")
async def get_team_activity(team_id: str, limit: int = 50):
    """Get team activity log"""
    try:
        logs = team_manager.get_activity_log(team_id, limit)
        
        return {
            "team_id": team_id,
            "activity": [
                {
                    "user_id": log.user_id,
                    "action": log.action,
                    "target": log.target,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# COMMENTING ROUTES

@router.post("/comments")
async def add_comment(request: AddCommentRequest):
    """Add a comment"""
    try:
        import uuid
        comment_id = str(uuid.uuid4())
        
        comment = commenting_system.add_comment(
            comment_id=comment_id,
            user_id=request.user_id,
            target_id=request.target_id,
            target_type=request.target_type,
            content=request.content,
            timestamp=request.timestamp,
            parent_id=request.parent_id
        )
        
        return {
            "comment_id": comment.comment_id,
            "status": comment.status.value,
            "mentions": comment.mentions,
            "created_at": comment.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comments/{target_id}")
async def get_comments(target_id: str, include_resolved: bool = False):
    """Get comments for target"""
    try:
        comments = commenting_system.get_comments(target_id, include_resolved)
        
        return {
            "target_id": target_id,
            "comments": [
                {
                    "comment_id": c.comment_id,
                    "user_id": c.user_id,
                    "content": c.content,
                    "timestamp": c.timestamp,
                    "status": c.status.value,
                    "parent_id": c.parent_id,
                    "mentions": c.mentions,
                    "created_at": c.created_at.isoformat()
                }
                for c in comments
            ],
            "count": len(comments)
        }
    except Exception as e:
        logger.error(f"Failed to get comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TEMPLATE ROUTES

@router.post("/templates")
async def create_template(creator_id: str, request: CreateTemplateRequest):
    """Create a video template"""
    try:
        import uuid
        template_id = str(uuid.uuid4())
        
        visibility = TemplateVisibility(request.visibility)
        
        template = template_manager.create_template(
            template_id=template_id,
            creator_id=creator_id,
            name=request.name,
            description=request.description,
            parameters=request.parameters,
            visibility=visibility,
            team_id=request.team_id,
            tags=request.tags
        )
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "visibility": template.visibility.value,
            "created_at": template.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_templates(user_id: Optional[str] = None, public_only: bool = False):
    """Get templates"""
    try:
        if public_only or not user_id:
            templates = template_manager.get_public_templates()
        else:
            templates = template_manager.get_user_templates(user_id)
        
        return {
            "templates": [
                {
                    "template_id": t.template_id,
                    "name": t.name,
                    "description": t.description,
                    "visibility": t.visibility.value,
                    "use_count": t.use_count,
                    "tags": t.tags
                }
                for t in templates
            ],
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# SCHEDULING ROUTES

@router.post("/schedule")

async def schedule_video(creator_id: str, request: ScheduleVideoRequest):
    """Schedule video publishing"""
    try:
        import uuid
        schedule_id = str(uuid.uuid4())
        
        publish_date = datetime.fromisoformat(request.publish_date)
        
        schedule = content_calendar.schedule_video(
            schedule_id=schedule_id,
            video_id=request.video_id,
            creator_id=creator_id,
            publish_date=publish_date,
            platforms=request.platforms
        )
        
        return {
            "schedule_id": schedule.schedule_id,
            "video_id": schedule.video_id,
            "publish_date": schedule.publish_date.isoformat(),
            "status": schedule.status.value
        }
    except Exception as e:
        logger.error(f"Failed to schedule video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar")
async def get_calendar(creator_id: str, year: int, month: int):
    """Get monthly calendar"""
    try:
        schedules = content_calendar.get_monthly_calendar(creator_id, year, month)
        
        return {
            "year": year,
            "month": month,
            "schedules": [
                {
                    "schedule_id": s.schedule_id,
                    "video_id": s.video_id,
                    "publish_date": s.publish_date.isoformat(),
                    "status": s.status.value,
                    "platforms": s.platforms
                }
                for s in schedules
            ],
            "count": len(schedules)
        }
    except Exception as e:
        logger.error(f"Failed to get calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# INTEGRATION ROUTES

@router.get("/integrations")
async def list_integrations():
    """List available integrations"""
    return {
        "integrations": [
            {"type": "youtube", "name": "YouTube", "available": True},
            {"type": "twitter", "name": "Twitter/X", "available": True},
            {"type": "instagram", "name": "Instagram", "available": True},
            {"type": "tiktok", "name": "TikTok", "available": True},
            {"type": "slack", "name": "Slack", "available": True}
        ]
    }


@router.post("/integrations/youtube/upload")
async def upload_to_youtube(
    user_id: str,
    video_id: str,
    title: str,
    description: str,
    tags: List[str]
):
    """Upload video to YouTube"""
    try:
        result = youtube_integration.upload_video(
            user_id=user_id,
            video_id=video_id,
            title=title,
            description=description,
            tags=tags
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to upload to YouTube: {e}")
        raise HTTPException(status_code=500, detail=str(e))
