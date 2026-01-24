"""
Client Setup Automation
One-command client creation with all configurations.
"""
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from app.core.logging import get_logger
from app.agency.client_service import AgencyClientService, AgencyClient, Agency
from app.analytics.revenue_dashboard import RevenueDashboard

logger = get_logger(__name__)


@dataclass
class ClientSetupConfig:
    """Configuration for automated client setup."""
    client_name: str
    agency_id: str = ""
    agency_name: str = ""
    agency_email: str = ""
    
    # Plan settings
    plan: str = "growth"  # starter, growth, agency
    monthly_fee: float = 10000
    videos_quota: int = 200
    
    # Content settings
    persona: str = "fast_explainer"
    visual_style: str = "minimal_facts"
    genre: str = "facts"
    audience: str = "genz_us"
    platforms: list = None
    
    # Controls
    lock_persona: bool = True
    lock_visual_style: bool = True
    max_retries: int = 2
    require_hook_approval: bool = False
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = ["youtube_shorts"]


PLAN_CONFIGS = {
    "starter": {"monthly_fee": 5000, "videos_quota": 50},
    "growth": {"monthly_fee": 10000, "videos_quota": 200},
    "agency": {"monthly_fee": 25000, "videos_quota": 500},
    "enterprise": {"monthly_fee": 50000, "videos_quota": 1000}
}


class ClientSetupAutomation:
    """
    Automated client setup - one command to production-ready.
    """
    
    def __init__(self):
        self.client_service = AgencyClientService()
        self.dashboard = RevenueDashboard()
    
    def setup_from_config(self, config: ClientSetupConfig) -> Dict:
        """
        Complete client setup from config.
        
        Args:
            config: ClientSetupConfig
            
        Returns:
            Setup result with IDs and status
        """
        logger.info(f"Starting automated setup for: {config.client_name}")
        result = {"status": "success", "steps": []}
        
        try:
            # Step 1: Get or create agency
            if config.agency_id:
                agency = self.client_service.get_agency(config.agency_id)
            else:
                agency = self.client_service.create_agency(
                    config.agency_name or f"{config.client_name} Agency",
                    config.agency_email or f"contact@{config.client_name.lower().replace(' ', '')}.com"
                )
            result["agency_id"] = agency.id
            result["steps"].append(f"✓ Agency: {agency.name}")
            
            # Step 2: Apply plan settings
            plan_config = PLAN_CONFIGS.get(config.plan, PLAN_CONFIGS["growth"])
            quota = config.videos_quota or plan_config["videos_quota"]
            fee = config.monthly_fee or plan_config["monthly_fee"]
            
            # Step 3: Create client
            client = self.client_service.create_client(
                agency.id,
                name=config.client_name,
                persona=config.persona,
                visual_style=config.visual_style,
                genre=config.genre,
                audience=config.audience,
                platforms=config.platforms,
                monthly_quota=quota,
                lock_persona=config.lock_persona,
                lock_visual_style=config.lock_visual_style,
                max_retries=config.max_retries,
                require_hook_approval=config.require_hook_approval
            )
            result["client_id"] = client.id
            result["steps"].append(f"✓ Client: {client.name}")
            
            # Step 4: Add to revenue dashboard
            self.dashboard.add_client(client.id, client.name, fee, quota)
            result["steps"].append(f"✓ Dashboard: ₹{fee}/mo, {quota} videos")
            
            # Step 5: Log setup
            result["setup_time"] = datetime.utcnow().isoformat()
            result["plan"] = config.plan
            
            logger.info(f"Setup complete for {config.client_name} in {len(result['steps'])} steps")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Setup failed: {e}")
        
        return result
    
    def setup_from_json(self, json_config: str) -> Dict:
        """Setup from JSON string."""
        data = json.loads(json_config)
        config = ClientSetupConfig(**data)
        return self.setup_from_config(config)
    
    def quick_setup(
        self,
        client_name: str,
        plan: str = "growth",
        persona: str = "fast_explainer"
    ) -> Dict:
        """Quick setup with minimal config."""
        config = ClientSetupConfig(
            client_name=client_name,
            plan=plan,
            persona=persona
        )
        return self.setup_from_config(config)
    
    def close(self):
        self.client_service.close()


def setup_client_cli():
    """CLI for quick client setup."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.automation.client_setup <client_name> [plan] [persona]")
        return
    
    name = sys.argv[1]
    plan = sys.argv[2] if len(sys.argv) > 2 else "growth"
    persona = sys.argv[3] if len(sys.argv) > 3 else "fast_explainer"
    
    automation = ClientSetupAutomation()
    result = automation.quick_setup(name, plan, persona)
    
    print("\n" + "=" * 50)
    print("CLIENT SETUP COMPLETE")
    print("=" * 50)
    for step in result.get("steps", []):
        print(f"  {step}")
    print(f"\nClient ID: {result.get('client_id')}")
    print(f"Agency ID: {result.get('agency_id')}")
    
    automation.close()


if __name__ == "__main__":
    setup_client_cli()
