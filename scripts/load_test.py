"""
Load Testing with Locust.
Simulates production traffic to validate performance and scalability.
"""
from locust import HttpUser, task, between, events
import random
import json
import logging

logger = logging.getLogger(__name__)


class VideoCreatorUser(HttpUser):
    """
    Simulated user for load testing.
    
    Simulates realistic user behavior:
    - Login/authentication
    - Browse videos
    - Create videos
    - Upload media
    - Check status
    """
    
    # Wait 1-5 seconds between tasks (realistic user behavior)
    wait_time = between(1, 5)
    
    # API host (set via command line)
    host = "https://api.ytvideocreator.com"
    
    # Test data
    access_token = None
    video_ids = []
    
    def on_start(self):
        """
        Called when user starts.
        Login and get access token.
        """
        self.login()
    
    def login(self):
        """Authenticate and get JWT token."""
        try:
            response = self.client.post(
                "/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": "load_test_client",
                    "client_secret": "load_test_secret"
                },
                name="/oauth/token (login)"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                logger.info("Login successful")
            else:
                logger.error(f"Login failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Login error: {e}")
    
    @task(5)
    def list_videos(self):
        """
        List user's videos (most common operation).
        Weight: 5 (50% of requests)
        """
        if not self.access_token:
            return
        
        self.client.get(
            "/api/videos",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/api/videos (list)"
        )
    
    @task(3)
    def get_video_details(self):
        """
        Get specific video details.
        Weight: 3 (30% of requests)
        """
        if not self.access_token or not self.video_ids:
            return
        
        video_id = random.choice(self.video_ids)
        
        self.client.get(
            f"/api/videos/{video_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/api/videos/:id (get)"
        )
    
    @task(1)
    def create_video(self):
        """
        Create new video.
        Weight: 1 (10% of requests)
        """
        if not self.access_token:
            return
        
        video_data = {
            "title": f"Load Test Video {random.randint(1, 10000)}",
            "description": "Automated load test video",
            "tags": ["test", "load", "automation"],
            "duration": random.randint(30, 300)
        }
        
        response = self.client.post(
            "/api/videos",
            json=video_data,
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/api/videos (create)"
        )
        
        if response.status_code == 201:
            data = response.json()
            video_id = data.get("id")
            if video_id:
                self.video_ids.append(video_id)
    
    @task(2)
    def update_video(self):
        """
        Update video metadata.
        Weight: 2 (20% of requests)
        """
        if not self.access_token or not self.video_ids:
            return
        
        video_id = random.choice(self.video_ids)
        
        update_data = {
            "title": f"Updated Video {random.randint(1, 1000)}",
            "description": "Updated description"
        }
        
        self.client.put(
            f"/api/videos/{video_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/api/videos/:id (update)"
        )
    
    @task(1)
    def delete_video(self):
        """
        Delete video.
        Weight: 1 (10% of requests - cleanup)
        """
        if not self.access_token or not self.video_ids:
            return
        
        if len(self.video_ids) > 10:  # Keep some videos
            video_id = self.video_ids.pop()
            
            self.client.delete(
                f"/api/videos/{video_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                name="/api/videos/:id (delete)"
            )
    
    @task(2)
    def health_check(self):
        """
        Health check endpoint.
        Weight: 2 (monitoring)
        """
        self.client.get(
            "/health/live",
            name="/health/live"
        )


class AdminUser(HttpUser):
    """Admin user performing administrative tasks."""
    
    wait_time = between(3, 10)
    host = "https://api.ytvideocreator.com"
    access_token = None
    
    def on_start(self):
        """Admin login."""
        response = self.client.post(
            "/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": "admin_client",
                "client_secret": "admin_secret"
            }
        )
        
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
    
    @task(5)
    def get_compliance_dashboard(self):
        """Check compliance dashboard."""
        if not self.access_token:
            return
        
        self.client.get(
            "/compliance/dashboard",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/compliance/dashboard"
        )
    
    @task(2)
    def get_metrics(self):
        """Get system metrics."""
        if not self.access_token:
            return
        
        self.client.get(
            "/compliance/metrics",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="/compliance/metrics"
        )


# Event handlers for custom logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    logger.info("Load test starting...")
    print("=" * 80)
    print("LOAD TEST STARTING")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    logger.info("Load test complete")
    print("=" * 80)
    print("LOAD TEST COMPLETE")
    print("=" * 80)
    
    # Print summary
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time}ms")
    print(f"Max Response Time: {stats.total.max_response_time}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")
    
    # Check if performance targets met
    p95 = stats.total.get_response_time_percentile(0.95)
    p99 = stats.total.get_response_time_percentile(0.99)
    
    print(f"\nPerformance Metrics:")
    print(f"p95 Response Time: {p95:.2f}ms (Target: < 200ms)")
    print(f"p99 Response Time: {p99:.2f}ms (Target: < 500ms)")
    
    if p95 < 200:
        print("✅ p95 target met!")
    else:
        print("❌ p95 target MISSED")
    
    if p99 < 500:
        print("✅ p99 target met!")
    else:
        print("❌ p99 target MISSED")


# Usage:
# Run basic load test:
# locust -f scripts/load_test.py --host=https://api.ytvideocreator.com

# Run headless with specific users:
# locust -f scripts/load_test.py \
#   --host=https://api.ytvideocreator.com \
#   --headless \
#   --users 1000 \
#   --spawn-rate 50 \
#   --run-time 10m

# Performance Targets:
# - 1000+ concurrent users
# - 10,000+ requests per minute
# - p95 response time < 200ms
# - p99 response time < 500ms
# - Error rate < 0.1%
