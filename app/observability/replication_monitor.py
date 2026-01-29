"""
Database replication lag monitor for Aurora Global Database.
Monitors and alerts on replication lag between regions.
"""
import logging
import psycopg2
from prometheus_client import Gauge
import time
from typing import Tuple

logger = logging.getLogger(__name__)

# Prometheus metrics
replication_lag_gauge = Gauge(
    'postgres_replication_lag_seconds',
    'Replication lag in seconds between primary and secondary',
    ['source_region', 'target_region']
)

replication_lag_bytes_gauge = Gauge(
    'postgres_replication_lag_bytes',
    'Replication lag in bytes',
    ['source_region', 'target_region']
)


class ReplicationMonitor:
    """
    Monitors Aurora Global Database replication lag.
    """
    
    def __init__(
        self,
        primary_endpoint: str,
        secondary_endpoint: str,
        db_name: str = "yt_video_creator",
        db_user: str = "postgres",
        db_password: str = None
    ):
        """
        Initialize replication monitor.
        
        Args:
            primary_endpoint: Primary cluster endpoint (us-east-1)
            secondary_endpoint: Secondary cluster endpoint (us-west-2)
            db_name: Database name
            db_user: Database user
            db_password: Database password
        """
        self.primary_endpoint = primary_endpoint
        self.secondary_endpoint = secondary_endpoint
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        
        logger.info(
            f"ReplicationMonitor initialized: "
            f"primary={primary_endpoint}, secondary={secondary_endpoint}"
        )
    
    def get_connection(self, endpoint: str):
        """Get database connection."""
        return psycopg2.connect(
            host=endpoint,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            connect_timeout=5
        )
    
    def get_current_lsn(self, endpoint: str) -> int:
        """
        Get current Log Sequence Number (LSN).
        
        Args:
            endpoint: Database endpoint
            
        Returns:
            Current LSN as integer
        """
        try:
            conn = self.get_connection(endpoint)
            cursor = conn.cursor()
            
            # Get current WAL LSN
            cursor.execute("SELECT pg_current_wal_lsn()")
            lsn_str = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Convert LSN to integer for comparison
            # Format: 0/3000060 → convert to bytes
            parts = lsn_str.split('/')
            lsn_int = (int(parts[0], 16) << 32) + int(parts[1], 16)
            
            return lsn_int
        
        except Exception as e:
            logger.error(f"Failed to get LSN from {endpoint}: {e}")
            return 0
    
    def get_replay_lsn(self, endpoint: str) -> int:
        """
        Get last replayed LSN on replica.
        
        Args:
            endpoint: Replica endpoint
            
        Returns:
            Last replayed LSN as integer
        """
        try:
            conn = self.get_connection(endpoint)
            cursor = conn.cursor()
            
            # Get last replayed WAL LSN
            cursor.execute("SELECT pg_last_wal_replay_lsn()")
            result = cursor.fetchone()
            
            if result and result[0]:
                lsn_str = result[0]
                parts = lsn_str.split('/')
                lsn_int = (int(parts[0], 16) << 32) + int(parts[1], 16)
            else:
                # Not a replica or no replication yet
                lsn_int = 0
            
            cursor.close()
            conn.close()
            
            return lsn_int
        
        except Exception as e:
            logger.error(f"Failed to get replay LSN from {endpoint}: {e}")
            return 0
    
    def calculate_lag(self) -> Tuple[int, float]:
        """
        Calculate replication lag.
        
        Returns:
            Tuple of (lag_bytes, lag_seconds_estimate)
        """
        # Get current LSN from primary
        primary_lsn = self.get_current_lsn(self.primary_endpoint)
        
        # Get replayed LSN from secondary
        secondary_lsn = self.get_replay_lsn(self.secondary_endpoint)
        
        # Calculate lag in bytes
        lag_bytes = primary_lsn - secondary_lsn
        
        # Estimate lag in seconds (rough estimate: 1 MB/s replication rate)
        # This is a rough estimate and varies based on network and load
        lag_seconds = lag_bytes / (1024 * 1024) if lag_bytes > 0 else 0
        
        return lag_bytes, lag_seconds
    
    def monitor_loop(self, interval: int = 15):
        """
        Continuously monitor replication lag.
        
        Args:
            interval: Check interval in seconds
        """
        logger.info(f"Starting replication monitoring (interval: {interval}s)")
        
        while True:
            try:
                lag_bytes, lag_seconds = self.calculate_lag()
                
                # Export metrics
                replication_lag_bytes_gauge.labels(
                    source_region='us-east-1',
                    target_region='us-west-2'
                ).set(lag_bytes)
                
                replication_lag_gauge.labels(
                    source_region='us-east-1',
                    target_region='us-west-2'
                ).set(lag_seconds)
                
                # Log warning if lag is high
                if lag_seconds > 5:
                    logger.warning(
                        f"High replication lag detected: {lag_seconds:.2f}s "
                        f"({lag_bytes} bytes)"
                    )
                else:
                    logger.debug(
                        f"Replication lag: {lag_seconds:.2f}s ({lag_bytes} bytes)"
                    )
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def get_lag_report(self) -> dict:
        """
        Get current replication lag report.
        
        Returns:
            Dictionary with lag metrics
        """
        lag_bytes, lag_seconds = self.calculate_lag()
        
        return {
            'lag_bytes': lag_bytes,
            'lag_seconds': lag_seconds,
            'lag_mb': lag_bytes / (1024 * 1024),
            'status': 'healthy' if lag_seconds < 5 else 'warning',
            'primary': self.primary_endpoint,
            'secondary': self.secondary_endpoint
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize monitor
    monitor = ReplicationMonitor(
        primary_endpoint="yt-video-creator-primary.cluster-xxx.us-east-1.rds.amazonaws.com",
        secondary_endpoint="yt-video-creator-secondary.cluster-yyy.us-west-2.rds.amazonaws.com",
        db_password="your-password"
    )
    
    # Get one-time report
    report = monitor.get_lag_report()
    print(f"Replication Lag Report: {report}")
    
    # Start continuous monitoring
    # monitor.monitor_loop(interval=15)
