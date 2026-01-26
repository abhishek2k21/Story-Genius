"""
Template System Models
Defines templates, versions, and configuration elements for reusable project structures.
"""
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import copy


class ElementType(str, Enum):
    """Types of template configuration elements"""
    FIXED = "fixed"  # Cannot be changed at instantiation
    VARIABLE = "variable"  # Must be provided at instantiation
    CONSTRAINED = "constrained"  # Can vary within defined bounds


@dataclass
class ConstraintBounds:
    """Defines bounds for constrained elements"""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None  # For enum-like constraints
    pattern: Optional[str] = None  # For string pattern matching


@dataclass
class TemplateElement:
    """Single configuration element in a template"""
    name: str
    element_type: ElementType
    value: Any = None  # Fixed value or default value
    bounds: Optional[ConstraintBounds] = None  # For constrained elements
    description: Optional[str] = None
    required: bool = True
    
    def to_dict(self) -> Dict:
        result = {
            "name": self.name,
            "element_type": self.element_type.value,
            "value": self.value,
            "description": self.description,
            "required": self.required
        }
        if self.bounds:
            result["bounds"] = {
                "min_value": self.bounds.min_value,
                "max_value": self.bounds.max_value,
                "allowed_values": self.bounds.allowed_values,
                "pattern": self.bounds.pattern
            }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemplateElement":
        bounds = None
        if "bounds" in data and data["bounds"]:
            bounds = ConstraintBounds(
                min_value=data["bounds"].get("min_value"),
                max_value=data["bounds"].get("max_value"),
                allowed_values=data["bounds"].get("allowed_values"),
                pattern=data["bounds"].get("pattern")
            )
        return cls(
            name=data["name"],
            element_type=ElementType(data["element_type"]),
            value=data.get("value"),
            bounds=bounds,
            description=data.get("description"),
            required=data.get("required", True)
        )


@dataclass
class TemplateConfig:
    """Configuration structure for a template version"""
    # Generation settings
    platform: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="platform",
        element_type=ElementType.FIXED,
        value="youtube_shorts"
    ))
    duration: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="duration",
        element_type=ElementType.CONSTRAINED,
        value=30,
        bounds=ConstraintBounds(min_value=5, max_value=180)
    ))
    voice: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="voice",
        element_type=ElementType.FIXED,
        value="en-US-GuyNeural"
    ))
    
    # Content settings
    genre: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="genre",
        element_type=ElementType.FIXED,
        value="educational"
    ))
    language: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="language",
        element_type=ElementType.FIXED,
        value="en"
    ))
    audience: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="audience",
        element_type=ElementType.FIXED,
        value="general"
    ))
    
    # Variable elements (must be provided)
    content: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="content",
        element_type=ElementType.VARIABLE,
        value=None,
        description="Topic or script content"
    ))
    
    # Optional style reference
    style_profile: TemplateElement = field(default_factory=lambda: TemplateElement(
        name="style_profile",
        element_type=ElementType.FIXED,
        value=None,
        required=False
    ))
    
    def get_all_elements(self) -> List[TemplateElement]:
        """Get all configuration elements"""
        return [
            self.platform, self.duration, self.voice,
            self.genre, self.language, self.audience,
            self.content, self.style_profile
        ]
    
    def get_fixed_elements(self) -> List[TemplateElement]:
        """Get only fixed elements"""
        return [e for e in self.get_all_elements() if e.element_type == ElementType.FIXED]
    
    def get_variable_elements(self) -> List[TemplateElement]:
        """Get only variable elements"""
        return [e for e in self.get_all_elements() if e.element_type == ElementType.VARIABLE]
    
    def get_constrained_elements(self) -> List[TemplateElement]:
        """Get only constrained elements"""
        return [e for e in self.get_all_elements() if e.element_type == ElementType.CONSTRAINED]
    
    def to_dict(self) -> Dict:
        return {
            "elements": [e.to_dict() for e in self.get_all_elements()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemplateConfig":
        config = cls()
        elements_data = data.get("elements", [])
        
        for elem_data in elements_data:
            elem = TemplateElement.from_dict(elem_data)
            # Map to config attributes
            if hasattr(config, elem.name):
                setattr(config, elem.name, elem)
        
        return config
    
    @classmethod
    def from_batch_config(cls, batch_config: Dict) -> "TemplateConfig":
        """Create template config from batch config"""
        return cls(
            platform=TemplateElement(
                name="platform",
                element_type=ElementType.FIXED,
                value=batch_config.get("platform", "youtube_shorts")
            ),
            duration=TemplateElement(
                name="duration",
                element_type=ElementType.CONSTRAINED,
                value=batch_config.get("duration", 30),
                bounds=ConstraintBounds(min_value=5, max_value=180)
            ),
            voice=TemplateElement(
                name="voice",
                element_type=ElementType.FIXED,
                value=batch_config.get("voice", "en-US-GuyNeural")
            ),
            genre=TemplateElement(
                name="genre",
                element_type=ElementType.FIXED,
                value=batch_config.get("genre", "educational")
            ),
            language=TemplateElement(
                name="language",
                element_type=ElementType.FIXED,
                value=batch_config.get("language", "en")
            ),
            audience=TemplateElement(
                name="audience",
                element_type=ElementType.FIXED,
                value=batch_config.get("audience", "general")
            ),
            content=TemplateElement(
                name="content",
                element_type=ElementType.VARIABLE,
                value=None,
                description="Topic or script content"
            ),
            style_profile=TemplateElement(
                name="style_profile",
                element_type=ElementType.FIXED,
                value=batch_config.get("style_profile"),
                required=False
            )
        )


@dataclass
class TemplateVersion:
    """Specific version of a template's configuration"""
    version: int = 1
    config: TemplateConfig = field(default_factory=TemplateConfig)
    change_description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "config": self.config.to_dict(),
            "change_description": self.change_description,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TemplateVersion":
        return cls(
            version=data.get("version", 1),
            config=TemplateConfig.from_dict(data.get("config", {})),
            change_description=data.get("change_description"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )


@dataclass
class Template:
    """Reusable project structure template"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    
    # Current version
    current_version: int = 1
    versions: List[TemplateVersion] = field(default_factory=list)
    
    # Source tracking
    source_type: Optional[str] = None  # "project", "batch", or "manual"
    source_id: Optional[str] = None
    
    # Ownership
    user_id: Optional[str] = None
    is_public: bool = False
    
    # Usage tracking
    usage_count: int = 0
    success_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Status
    active: bool = True
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.versions:
            # Initialize with first version
            self.versions = [TemplateVersion(version=1)]
    
    def get_current_config(self) -> TemplateConfig:
        """Get configuration for current version"""
        for v in self.versions:
            if v.version == self.current_version:
                return v.config
        return self.versions[-1].config if self.versions else TemplateConfig()
    
    def get_version(self, version: int) -> Optional[TemplateVersion]:
        """Get specific version"""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def create_new_version(
        self,
        config: TemplateConfig,
        change_description: str = None
    ) -> TemplateVersion:
        """Create new version with updated config"""
        new_version_num = self.current_version + 1
        
        new_version = TemplateVersion(
            version=new_version_num,
            config=config,
            change_description=change_description
        )
        
        self.versions.append(new_version)
        self.current_version = new_version_num
        self.updated_at = datetime.now()
        
        return new_version
    
    def increment_usage(self, success: bool = True):
        """Track template usage"""
        self.usage_count += 1
        if success:
            self.success_count += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
            "source_type": self.source_type,
            "source_id": self.source_id,
            "user_id": self.user_id,
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "success_rate": round(self.success_rate * 100, 1),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active": self.active,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Template":
        template = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description"),
            current_version=data.get("current_version", 1),
            source_type=data.get("source_type"),
            source_id=data.get("source_id"),
            user_id=data.get("user_id"),
            is_public=data.get("is_public", False),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            active=data.get("active", True),
            tags=data.get("tags", [])
        )
        
        # Reconstruct versions
        template.versions = [
            TemplateVersion.from_dict(v) for v in data.get("versions", [])
        ]
        
        if not template.versions:
            template.versions = [TemplateVersion(version=1)]
        
        return template
