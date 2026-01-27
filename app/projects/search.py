"""
Project Search
Advanced search with multiple criteria and facets.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import threading


@dataclass
class SearchCriteria:
    """Search criteria for projects"""
    query: str = ""
    folder_id: str = None
    folder_recursive: bool = False
    tags: List[str] = field(default_factory=list)
    tag_match: str = "any"  # any, all
    status: str = None
    is_favorite: bool = None
    is_archived: bool = None
    platform: str = None
    template_id: str = None
    batch_id: str = None
    created_after: datetime = None
    created_before: datetime = None
    updated_after: datetime = None
    updated_before: datetime = None
    has_output: bool = None
    sort: str = "created_desc"
    page: int = 1
    page_size: int = 20


@dataclass
class SearchResult:
    """Search result with pagination and facets"""
    results: List[Dict]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "results": self.results,
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "facets": self.facets
        }


@dataclass
class SavedSearch:
    """Saved search for quick access"""
    search_id: str
    user_id: str
    name: str
    criteria: Dict
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "search_id": self.search_id,
            "name": self.name,
            "criteria": self.criteria,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat()
        }


class ProjectSearchService:
    """Project search service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._saved_searches: Dict[str, SavedSearch] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def search(
        self,
        projects: List[Dict],
        criteria: SearchCriteria,
        tag_service=None
    ) -> SearchResult:
        """Search projects with criteria"""
        results = projects.copy()
        
        # Text search
        if criteria.query:
            query_lower = criteria.query.lower()
            results = [p for p in results if 
                       query_lower in p.get("name", "").lower() or
                       query_lower in p.get("description", "").lower()]
        
        # Folder filter
        if criteria.folder_id:
            results = [p for p in results if p.get("folder_id") == criteria.folder_id]
        
        # Tag filter
        if criteria.tags and tag_service:
            matching_ids = set(tag_service.get_projects_by_tags(
                criteria.tags, 
                match_all=(criteria.tag_match == "all")
            ))
            results = [p for p in results if p.get("project_id") in matching_ids]
        
        # Status filter
        if criteria.status:
            results = [p for p in results if p.get("status") == criteria.status]
        
        # Favorite filter
        if criteria.is_favorite is not None:
            results = [p for p in results if p.get("is_favorite") == criteria.is_favorite]
        
        # Archive filter
        if criteria.is_archived is not None:
            results = [p for p in results if p.get("is_archived") == criteria.is_archived]
        
        # Platform filter
        if criteria.platform:
            results = [p for p in results if p.get("platform") == criteria.platform]
        
        # Date filters
        if criteria.created_after:
            results = [p for p in results if 
                       datetime.fromisoformat(p.get("created_at", "")) >= criteria.created_after]
        
        if criteria.created_before:
            results = [p for p in results if 
                       datetime.fromisoformat(p.get("created_at", "")) <= criteria.created_before]
        
        # Calculate facets before pagination
        facets = self._calculate_facets(results)
        
        # Sort
        results = self._sort_results(results, criteria.sort)
        
        # Pagination
        total_count = len(results)
        total_pages = (total_count + criteria.page_size - 1) // criteria.page_size
        start = (criteria.page - 1) * criteria.page_size
        end = start + criteria.page_size
        results = results[start:end]
        
        return SearchResult(
            results=results,
            total_count=total_count,
            page=criteria.page,
            page_size=criteria.page_size,
            total_pages=total_pages,
            facets=facets
        )
    
    def _sort_results(self, results: List[Dict], sort: str) -> List[Dict]:
        """Sort results"""
        sort_map = {
            "created_desc": ("created_at", True),
            "created_asc": ("created_at", False),
            "updated_desc": ("updated_at", True),
            "updated_asc": ("updated_at", False),
            "name_asc": ("name", False),
            "name_desc": ("name", True)
        }
        
        field, reverse = sort_map.get(sort, ("created_at", True))
        return sorted(results, key=lambda p: p.get(field, ""), reverse=reverse)
    
    def _calculate_facets(self, results: List[Dict]) -> Dict:
        """Calculate facet aggregations"""
        facets = {
            "by_status": {},
            "by_platform": {},
            "by_folder": {}
        }
        
        for p in results:
            status = p.get("status", "unknown")
            facets["by_status"][status] = facets["by_status"].get(status, 0) + 1
            
            platform = p.get("platform", "unknown")
            facets["by_platform"][platform] = facets["by_platform"].get(platform, 0) + 1
            
            folder = p.get("folder_id", "root")
            facets["by_folder"][folder] = facets["by_folder"].get(folder, 0) + 1
        
        return facets
    
    # Saved searches
    def save_search(
        self,
        user_id: str,
        name: str,
        criteria: Dict,
        is_default: bool = False
    ) -> SavedSearch:
        """Save a search"""
        search = SavedSearch(
            search_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            criteria=criteria,
            is_default=is_default
        )
        
        with self._lock:
            self._saved_searches[search.search_id] = search
        
        return search
    
    def list_saved_searches(self, user_id: str) -> List[SavedSearch]:
        """List saved searches for user"""
        return [s for s in self._saved_searches.values() if s.user_id == user_id]
    
    def delete_saved_search(self, search_id: str, user_id: str) -> bool:
        """Delete saved search"""
        search = self._saved_searches.get(search_id)
        if search and search.user_id == user_id:
            del self._saved_searches[search_id]
            return True
        return False


project_search_service = ProjectSearchService()
