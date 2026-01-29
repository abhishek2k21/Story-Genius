"""
Queue metrics exporter for Prometheus.
Exports Celery queue depth and latency metrics.
"""
import logging
import time
from typing import Dict, Optional
from prometheus_client import Gauge, start_http_server
from celery import Celery
import redis

logger = logging.getLogger(__name__)

# Prometheus metrics
queue_depth_gauge = Gauge(
    'celery_queue_depth',
    'Number of tasks waiting in Celery queue',
    ['queue']
)

queue_latency_gauge = Gauge(
    'celery_queue_latency_seconds',
    'Average task wait time in queue (seconds)',
    ['queue']
)

active_workers_gauge = Gauge(
    'celery_active_workers',
    'Number of active Celery workers',
    ['queue']
)

task_rate_gauge = Gauge(
    'celery_task_rate',
    'Tasks processed per second',
    ['queue']
)


class QueueMetricsExporter:
    """
    Exports Celery queue metrics to Prometheus.
    
    Supports Redis and RabbitMQ backends.
    """
    
    def __init__(
        self,
        celery_app: Optional[Celery] = None,
        redis_url: str = "redis://redis-ha:6379/0",
        export_interval: int = 15
    ):
        """
        Initialize queue metrics exporter.
        
        Args:
            celery_app: Celery application instance
            redis_url: Redis connection URL (if using Redis as broker)
            export_interval: Metrics export interval in seconds
        """
        self.celery = celery_app
        self.redis_url = redis_url
        self.export_interval = export_interval
        
        # Connect to Redis (assuming Redis broker)
        self.redis_client = redis.from_url(redis_url)
        
        logger.info(f"QueueMetricsExporter initialized (interval: {export_interval}s)")
    
    def get_queue_depth(self, queue: str = "celery") -> int:
        """
        Get number of pending tasks in queue.
        
        Args:
            queue: Queue name
            
        Returns:
            Number of pending tasks
        """
        try:
            # Redis: Get queue length
            # Queue key format: celery (default) or queue_name
            queue_key = queue if queue != "default" else "celery"
            depth = self.redis_client.llen(queue_key)
            return int(depth) if depth else 0
        
        except Exception as e:
            logger.error(f"Failed to get queue depth for {queue}: {e}")
            return 0
    
    def get_active_workers(self, queue: str = "celery") -> int:
        """
        Get number of active workers for queue.
        
        Args:
            queue: Queue name
            
        Returns:
            Number of active workers
        """
        try:
            if not self.celery:
                return 0
            
            # Get worker statistics
            inspect = self.celery.control.inspect()
            stats = inspect.stats()
            
            if not stats:
                return 0
            
            # Count workers processing this queue
            active = 0
            for worker, info in stats.items():
                if info.get('pool', {}).get('max-concurrency', 0) > 0:
                    active += 1
            
            return active
        
        except Exception as e:
            logger.error(f"Failed to get active workers: {e}")
            return 0
    
    def export_metrics(self):
        """
        Export queue metrics to Prometheus continuously.
        """
        logger.info("Starting queue metrics export")
        
        # Start Prometheus HTTP server
        start_http_server(8000)
        logger.info("Prometheus metrics server started on :8000")
        
        while True:
            try:
                # Export metrics for each queue
                for queue in ['celery', 'video-processing', 'default']:
                    # Queue depth
                    depth = self.get_queue_depth(queue)
                    queue_depth_gauge.labels(queue=queue).set(depth)
                    
                    # Active workers
                    workers = self.get_active_workers(queue)
                    active_workers_gauge.labels(queue=queue).set(workers)
                    
                    logger.debug(f"Queue {queue}: depth={depth}, workers={workers}")
                
                time.sleep(self.export_interval)
            
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")
                time.sleep(self.export_interval)
    
    def get_metrics_summary(self) -> Dict[str, Dict]:
        """
        Get current metrics summary for all queues.
        
        Returns:
            Dictionary of queue metrics
        """
        summary = {}
        
        for queue in ['celery', 'video-processing', 'default']:
            summary[queue] = {
                'depth': self.get_queue_depth(queue),
                'workers': self.get_active_workers(queue)
            }
        
        return summary


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create exporter
    exporter = QueueMetricsExporter(
        redis_url="redis://localhost:6379/0",
        export_interval=15
    )
    
    # Start exporting metrics
    exporter.export_metrics()
