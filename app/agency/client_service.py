"""
Agency Client Service
Manages agency clients with quotas, personas, and batch generation.
"""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from app.core.logging import get_logger
from app.core.models import Job
from app.orchestrator.service import OrchestratorService

logger = get_logger(__name__)


@dataclass
class AgencyClient:
    """
    A client managed by an agency.
    Each client has their own quota, settings, and content.
    """
    id: str
    name: str
    agency_id: str
    
    # Content settings
    default_persona: str = "fast_explainer"
    default_visual_style: str = "minimal_facts"
    platforms: List[str] = field(default_factory=lambda: ["youtube_shorts"])
    genre: str = "facts"
    audience: str = "genz_us"
    
    # Quotas
    monthly_quota: int = 200
    used_this_month: int = 0
    
    # Controls (human-in-the-loop)
    require_hook_approval: bool = False
    lock_persona: bool = False
    lock_visual_style: bool = False
    max_retries: int = 2
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_generation: datetime = None
    total_videos_generated: int = 0
    
    @property
    def remaining_quota(self) -> int:
        return max(0, self.monthly_quota - self.used_this_month)
    
    def can_generate(self, count: int = 1) -> tuple:
        """Check if client can generate videos."""
        if self.remaining_quota < count:
            return False, f"Quota exceeded. Remaining: {self.remaining_quota}"
        return True, "OK"
    
    def record_generation(self, count: int = 1):
        """Record video generation."""
        self.used_this_month += count
        self.total_videos_generated += count
        self.last_generation = datetime.utcnow()


@dataclass 
class Agency:
    """
    An agency managing multiple clients.
    """
    id: str
    name: str
    email: str
    
    # Settings
    default_monthly_client_quota: int = 200
    max_clients: int = 20
    
    # Billing
    plan: str = "agency"
    is_active: bool = True
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BatchResult:
    """Result of a batch generation."""
    client_id: str
    batch_id: str
    requested: int
    successful: int
    failed: int
    job_ids: List[str]
    total_time_sec: float
    avg_score: float


class AgencyClientService:
    """
    Service for managing agency clients and batch generation.
    """
    
    def __init__(self):
        self._agencies: Dict[str, Agency] = {}
        self._clients: Dict[str, AgencyClient] = {}
        self.orchestrator = OrchestratorService()
    
    # ============== Agency Management ==============
    
    def create_agency(self, name: str, email: str) -> Agency:
        """Create a new agency."""
        agency_id = str(uuid.uuid4())[:8]
        
        agency = Agency(
            id=agency_id,
            name=name,
            email=email
        )
        
        self._agencies[agency_id] = agency
        logger.info(f"Created agency: {name} ({agency_id})")
        
        return agency
    
    def get_agency(self, agency_id: str) -> Optional[Agency]:
        """Get agency by ID."""
        return self._agencies.get(agency_id)
    
    # ============== Client Management ==============
    
    def create_client(
        self,
        agency_id: str,
        name: str,
        **settings
    ) -> AgencyClient:
        """Create a client for an agency."""
        agency = self.get_agency(agency_id)
        if not agency:
            raise ValueError(f"Agency not found: {agency_id}")
        
        client_id = f"{agency_id}_{str(uuid.uuid4())[:6]}"
        
        client = AgencyClient(
            id=client_id,
            name=name,
            agency_id=agency_id,
            monthly_quota=settings.get("monthly_quota", agency.default_monthly_client_quota),
            default_persona=settings.get("persona", "fast_explainer"),
            default_visual_style=settings.get("visual_style", "minimal_facts"),
            platforms=settings.get("platforms", ["youtube_shorts"]),
            genre=settings.get("genre", "facts"),
            audience=settings.get("audience", "genz_us"),
            require_hook_approval=settings.get("require_hook_approval", False),
            lock_persona=settings.get("lock_persona", False),
            lock_visual_style=settings.get("lock_visual_style", False),
            max_retries=settings.get("max_retries", 2)
        )
        
        self._clients[client_id] = client
        logger.info(f"Created client: {name} for agency {agency_id}")
        
        return client
    
    def get_client(self, client_id: str) -> Optional[AgencyClient]:
        """Get client by ID."""
        return self._clients.get(client_id)
    
    def list_clients(self, agency_id: str) -> List[AgencyClient]:
        """List all clients for an agency."""
        return [c for c in self._clients.values() if c.agency_id == agency_id]
    
    def update_client_settings(self, client_id: str, **settings) -> bool:
        """Update client settings."""
        client = self.get_client(client_id)
        if not client:
            return False
        
        for key, value in settings.items():
            if hasattr(client, key):
                setattr(client, key, value)
        
        logger.info(f"Updated client {client_id} settings")
        return True
    
    # ============== Batch Generation ==============
    
    def generate_batch(
        self,
        client_id: str,
        topics: List[str] = None,
        count: int = 10
    ) -> BatchResult:
        """
        Generate a batch of videos for a client.
        
        Args:
            client_id: Target client
            topics: Optional list of topics
            count: Number of videos to generate
            
        Returns:
            BatchResult with all job results
        """
        import time
        start = time.time()
        
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        # Check quota
        can, msg = client.can_generate(count)
        if not can:
            raise ValueError(msg)
        
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting batch {batch_id} for client {client.name}: {count} videos")
        
        # Default topics if not provided
        if not topics:
            topics = [f"Amazing {client.genre} fact #{i+1}" for i in range(count)]
        
        job_ids = []
        successful = 0
        failed = 0
        scores = []
        
        for i, topic in enumerate(topics[:count]):
            try:
                # Build job config from client settings
                config = {
                    "platform": client.platforms[0] if client.platforms else "youtube_shorts",
                    "audience": client.audience,
                    "genre": client.genre,
                    "duration": 30,
                    "topic": topic
                }
                
                # Apply client controls
                # Note: These would be passed to orchestrator in full implementation
                
                job = self.orchestrator.create_job(config)
                job_ids.append(job.id)
                
                success = self.orchestrator.start_job(job.id)
                
                if success:
                    successful += 1
                    final_job = self.orchestrator.get_job(job.id)
                    if final_job and final_job.total_score:
                        scores.append(final_job.total_score)
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Batch job {i+1} failed: {e}")
                failed += 1
        
        # Record generation
        client.record_generation(successful)
        
        elapsed = time.time() - start
        avg_score = sum(scores) / len(scores) if scores else 0
        
        result = BatchResult(
            client_id=client_id,
            batch_id=batch_id,
            requested=count,
            successful=successful,
            failed=failed,
            job_ids=job_ids,
            total_time_sec=round(elapsed, 2),
            avg_score=round(avg_score, 3)
        )
        
        logger.info(f"Batch {batch_id} complete: {successful}/{count} successful, avg score {avg_score:.2f}")
        
        return result
    
    def get_client_stats(self, client_id: str) -> Dict:
        """Get statistics for a client."""
        client = self.get_client(client_id)
        if not client:
            return {"error": "Client not found"}
        
        return {
            "client_id": client_id,
            "name": client.name,
            "quota": {
                "monthly": client.monthly_quota,
                "used": client.used_this_month,
                "remaining": client.remaining_quota
            },
            "settings": {
                "persona": client.default_persona,
                "visual_style": client.default_visual_style,
                "platforms": client.platforms
            },
            "controls": {
                "require_hook_approval": client.require_hook_approval,
                "lock_persona": client.lock_persona,
                "max_retries": client.max_retries
            },
            "stats": {
                "total_videos": client.total_videos_generated,
                "last_generation": client.last_generation.isoformat() if client.last_generation else None
            }
        }
    
    def close(self):
        """Close orchestrator connection."""
        self.orchestrator.close()
