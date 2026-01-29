"""
Load Testing Suite using Locust.
Simulate realistic user traffic and measure performance under load.
"""
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import random
import logging

logger = logging.getLogger(__name__)


class VideoCreatorUser(HttpUser):
    """
    Simulates a typical Video Creator platform user.
    
    User behavior:
    - Login on start
    - View dashboard frequently (most common action)
    - List videos regularly
    - View analytics periodically
    - Create videos occasionally
    - Upload videos rarely (resource intensive)
    """
    
    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when user starts - login."""
        self.login()
    
    def login(self):
        """Authenticate user."""
        # Use test user credentials
        user_num = random.randint(1, 1000)
        
        response = self.client.post("/api/auth/login", json={
            "email": f"testuser{user_num}@example.com",
            "password": "TestPassword123!"
        })
        
        if response.status_code == 200:
            # Store auth token
            self.auth_token = response.json().get("token")
            logger.info(f"User {user_num} logged in successfully")
        else:
            logger.error(f"Login failed for user {user_num}")
            raise StopUser()
    
    @task(5)
    def view_dashboard(self):
        """
        View dashboard - most common action (weight 5).
        
        Fetches:
        - User metrics
        - Recent videos
        - Quick stats
        """
        self.client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="/api/dashboard"
        )
    
    @task(3)
    def list_videos(self):
        """
        List videos - common action (weight 3).
        
        Pagination test - fetches different pages.
        """
        page = random.randint(1, 5)
        
        self.client.get(
            f"/api/videos?page={page}&limit=20",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="/api/videos?page={page}"
        )
    
    @task(2)
    def view_analytics(self):
        """
        View analytics - periodic action (weight 2).
        
        Tests different time periods.
        """
        period = random.choice(["day", "week", "month", "year"])
        
        self.client.get(
            f"/api/analytics?period={period}",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name=f"/api/analytics?period={period}"
        )
    
    @task(2)
    def search_videos(self):
        """Search videos - periodic action (weight 2)."""
        queries = ["tutorial", "vlog", "review", "cooking", "gaming"]
        query = random.choice(queries)
        
        self.client.get(
            f"/api/videos/search?q={query}",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="/api/videos/search"
        )
    
    @task(1)
    def view_video_detail(self):
        """View single video - occasional action (weight 1)."""
        # Random video ID
        video_id = f"video-{random.randint(1, 1000)}"
        
        self.client.get(
            f"/api/videos/{video_id}",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="/api/videos/:id"
        )
    
    @task(1)
    def create_video(self):
        """
        Create video metadata - occasional action (weight 1).
        
        Note: Not uploading actual file in load test.
        """
        self.client.post(
            "/api/videos",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            json={
                "title": f"Load Test Video {random.randint(1, 10000)}",
                "description": "This is a test video created during load testing",
                "tags": ["test", "load-test"]
            },
            name="/api/videos [POST]"
        )
    
    @task(1)
    def update_profile(self):
        """Update user profile - occasional action (weight 1)."""
        self.client.put(
            "/api/users/profile",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            json={
                "first_name": "Test",
                "last_name": "User",
                "bio": "Load testing user"
            },
            name="/api/users/profile [PUT]"
        )
    
    @task(0.5)
    def generate_report(self):
        """Generate analytics report - rare action (weight 0.5)."""
        self.client.post(
            "/api/reports/generate",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            json={
                "name": "Load Test Report",
                "metrics": ["views", "engagement"],
                "period": "week"
            },
            name="/api/reports/generate [POST]"
        )


class GraphQLUser(HttpUser):
    """Test GraphQL API performance."""
    
    wait_time = between(1, 3)
    
    @task
    def query_videos(self):
        """GraphQL query for videos."""
        query = """
        query GetVideos {
            videos(page: 1, limit: 20) {
                edges {
                    node {
                        id
                        title
                        views
                        likes
                    }
                }
                pageInfo {
                    hasNextPage
                }
            }
        }
        """
        
        self.client.post(
            "/graphql",
            json={"query": query},
            name="GraphQL: videos"
        )


# Event handlers for custom metrics

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    logger.info("=" * 50)
    logger.info("LOAD TEST STARTING")
    logger.info(f"Target: {environment.host}")
    logger.info("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test ends."""
    stats = environment.stats
    
    logger.info("=" * 50)
    logger.info("LOAD TEST COMPLETE")
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Error rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"Avg response time: {stats.total.avg_response_time:.0f}ms")
    logger.info(f"p50: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    logger.info(f"p95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    logger.info(f"p99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    logger.info(f"RPS: {stats.total.total_rps:.1f}")
    logger.info("=" * 50)
    
    # Check if performance targets met
    p95 = stats.total.get_response_time_percentile(0.95)
    error_rate = stats.total.fail_ratio
    
    if p95 > 200:
        logger.warning(f"⚠️  p95 ({p95:.0f}ms) exceeds target (200ms)")
    else:
        logger.info(f"✅ p95 ({p95:.0f}ms) meets target")
    
    if error_rate > 0.001:  # 0.1%
        logger.warning(f"⚠️  Error rate ({error_rate*100:.2f}%) exceeds target (0.1%)")
    else:
        logger.info(f"✅ Error rate ({error_rate*100:.2f}%) meets target")


# Custom task sets for specific scenarios

class PeakTrafficUser(HttpUser):
    """Simulates peak traffic scenario."""
    wait_time = between(0.5, 2)  # Faster user actions
    
    @task(10)
    def rapid_dashboard_views(self):
        """Rapidly view dashboard."""
        self.client.get("/api/dashboard")
    
    @task(5)
    def rapid_video_list(self):
        """Rapidly list videos."""
        self.client.get("/api/videos")


# Run commands:
"""
# Basic load test - 100 users
locust -f load_test.py --users 100 --spawn-rate 10 --host https://api.ytvideocreator.com

# Production scale test - 10,000 users
locust -f load_test.py --users 10000 --spawn-rate 100 --host https://api.ytvideocreator.com --run-time 10m

# Peak traffic test
locust -f load_test.py --users 5000 --spawn-rate 200 --host https://api.ytvideocreator.com --user-classes PeakTrafficUser

# GraphQL only test
locust -f load_test.py --users 1000 --spawn-rate 50 --host https://api.ytvideocreator.com --user-classes GraphQLUser

# Headless mode with HTML report
locust -f load_test.py --headless --users 10000 --spawn-rate 100 --run-time 10m --html report.html
"""

# Performance Targets
"""
Targets:
  - 10,000 concurrent users
  - p50 response time: < 50ms
  - p95 response time: < 200ms
  - p99 response time: < 500ms
  - Error rate: < 0.1%
  - Throughput: > 5,000 req/sec
  
Infrastructure Targets:
  - CPU utilization: < 70%
  - Memory utilization: < 80%
  - Database connections: < 500
  - Cache hit rate: > 90%
"""
