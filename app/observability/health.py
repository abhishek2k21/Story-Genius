"""
Health Monitoring System
Component health checks and system status.
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time
import asyncio


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    status: HealthStatus
    latency_ms: int
    message: str = ""
    last_success: datetime = None
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "last_success": self.last_success.isoformat() if self.last_success else None
        }


@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    version: str
    uptime_seconds: int
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "components": [c.to_dict() for c in self.components]
        }


class HealthChecker:
    """Component health checker"""
    
    def __init__(self, name: str, check_fn: Callable, timeout: float = 5.0):
        self.name = name
        self.check_fn = check_fn
        self.timeout = timeout
        self.last_success: Optional[datetime] = None
    
    async def check(self) -> ComponentHealth:
        """Run health check"""
        start = time.time()
        
        try:
            # Run check with timeout
            if asyncio.iscoroutinefunction(self.check_fn):
                result = await asyncio.wait_for(self.check_fn(), timeout=self.timeout)
            else:
                result = self.check_fn()
            
            latency = int((time.time() - start) * 1000)
            
            if result.get("healthy", True):
                self.last_success = datetime.utcnow()
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message=result.get("message", "OK"),
                    last_success=self.last_success
                )
            else:
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message=result.get("message", "Check failed"),
                    last_success=self.last_success
                )
        
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=int(self.timeout * 1000),
                message="Health check timed out",
                last_success=self.last_success
            )
        
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e),
                last_success=self.last_success
            )


class HealthMonitor:
    """Central health monitoring orchestrator"""
    
    _instance = None
    _start_time: datetime = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._checkers: List[HealthChecker] = []
            cls._instance._start_time = datetime.utcnow()
            cls._instance._version = "1.0.0"
        return cls._instance
    
    def register(self, name: str, check_fn: Callable, timeout: float = 5.0):
        """Register a health check"""
        self._checkers.append(HealthChecker(name, check_fn, timeout))
    
    async def check_all(self) -> SystemHealth:
        """Run all health checks"""
        component_healths = []
        
        for checker in self._checkers:
            health = await checker.check()
            component_healths.append(health)
        
        # Determine overall status
        statuses = [c.status for c in component_healths]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        uptime = int((datetime.utcnow() - self._start_time).total_seconds())
        
        return SystemHealth(
            status=overall,
            timestamp=datetime.utcnow(),
            components=component_healths,
            version=self._version,
            uptime_seconds=uptime
        )
    
    def liveness(self) -> Dict:
        """Quick liveness check"""
        return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    
    def readiness(self) -> Dict:
        """Readiness check (sync, basic)"""
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


# Singleton instance
health_monitor = HealthMonitor()


# Built-in health checks
def check_memory() -> Dict:
    """Check memory usage"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        usage_percent = mem.percent
        
        return {
            "healthy": usage_percent < 85,
            "message": f"Memory usage: {usage_percent}%"
        }
    except ImportError:
        return {"healthy": True, "message": "Memory check not available"}


def check_disk() -> Dict:
    """Check disk space"""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        free_percent = 100 - disk.percent
        
        return {
            "healthy": free_percent > 10,
            "message": f"Disk free: {free_percent:.1f}%"
        }
    except ImportError:
        return {"healthy": True, "message": "Disk check not available"}


def check_engine_registry() -> Dict:
    """Check engine registry"""
    try:
        from app.engines.registry import EngineRegistry
        engines = EngineRegistry.list_all()
        count = len(engines)
        
        return {
            "healthy": count > 0,
            "message": f"{count} engines registered"
        }
    except Exception as e:
        return {"healthy": False, "message": str(e)}


# Register default checks
health_monitor.register("memory", check_memory)
health_monitor.register("disk", check_disk)
health_monitor.register("engines", check_engine_registry)
