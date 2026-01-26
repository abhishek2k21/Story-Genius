Week 20: Backend-Frontend Integration & Production Deployment
Goal: Connect your React dashboard to the FastAPI backend and deploy both to production

Day 1: CORS & API Client Setup
Why: Your frontend (React) and backend (FastAPI) need to communicate across origins
Tasks:

Configure CORS properly in FastAPI
Create API client in React with environment variables
Test connection with health check endpoint

Backend Code:
python# app/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Story Genius API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "https://yourdomain.vercel.app",  # Production frontend
        "https://yourdomain.com"  # Custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Add CORS headers to error responses too
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )
Frontend Code:
typescript// frontend/src/lib/api-client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string; version: string }>('/health');
  }

  // Job endpoints
  async createJob(data: CreateJobRequest) {
    return this.request<{ job_id: string }>('/v1/shorts/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getJobStatus(jobId: string) {
    return this.request<JobStatusResponse>(`/v1/jobs/${jobId}`);
  }

  async getJobVideo(jobId: string) {
    return this.request<JobVideoResponse>(`/v1/jobs/${jobId}/video`);
  }
}

export const apiClient = new ApiClient();

// Type definitions
export interface CreateJobRequest {
  platform: string;
  audience: string;
  topic: string;
  duration?: number;
  tone?: string;
  language?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress?: number;
  video_url?: string;
  error?: string;
  created_at: string;
}

export interface JobVideoResponse {
  job_id: string;
  status: string;
  final_video: string;
  scene_videos: Array<{ scene: number; url: string }>;
  audio: Array<{ scene: number; url: string }>;
  created_at: string;
}
Environment Setup:
bash# frontend/.env.development
VITE_API_BASE_URL=http://localhost:8000

# frontend/.env.production
VITE_API_BASE_URL=https://api.yourdomain.com
Test Connection:
typescript// frontend/src/components/HealthCheck.tsx
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function HealthCheck() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.healthCheck(),
  });

  if (isLoading) return <div>Checking API...</div>;
  if (error) return <div className="text-red-500">API Offline ❌</div>;
  
  return (
    <div className="text-green-500">
      API Online ✅ (v{data?.version})
    </div>
  );
}
Verify:
bash# Terminal 1: Start backend
uvicorn app.api.main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev

# Visit http://localhost:5173 and check if HealthCheck shows green
Deliverable: Frontend and backend communicating successfully

Day 2: Connect Video Creation Studio to Real API
Tasks:

Wire up the /create page to actual job creation endpoint
Add real-time job status polling
Show video player when generation completes

Code:
typescript// frontend/src/pages/Create.tsx
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { VideoPlayer } from '@/components/VideoPlayer';

export function Create() {
  const [topic, setTopic] = useState('');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Create job mutation
  const createJobMutation = useMutation({
    mutationFn: (data: { topic: string }) => 
      apiClient.createJob({
        platform: 'youtube_shorts',
        audience: 'general_adult',
        topic: data.topic,
        duration: 30,
      }),
    onSuccess: (response) => {
      setCurrentJobId(response.job_id);
    },
  });

  // Poll job status every 2 seconds if job exists
  const { data: jobStatus } = useQuery({
    queryKey: ['job-status', currentJobId],
    queryFn: () => apiClient.getJobStatus(currentJobId!),
    enabled: !!currentJobId,
    refetchInterval: (data) => {
      // Stop polling if completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  // Fetch video details when completed
  const { data: videoData } = useQuery({
    queryKey: ['job-video', currentJobId],
    queryFn: () => apiClient.getJobVideo(currentJobId!),
    enabled: jobStatus?.status === 'completed',
  });

  const handleGenerate = () => {
    if (topic.trim()) {
      createJobMutation.mutate({ topic });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create Video</h1>
        <p className="text-muted-foreground">
          Generate a short video from your idea
        </p>
      </div>

      {/* Input Form */}
      <div className="flex gap-2">
        <Input
          placeholder="Enter your video topic..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
          disabled={createJobMutation.isPending || !!currentJobId}
        />
        <Button
          onClick={handleGenerate}
          disabled={!topic.trim() || createJobMutation.isPending || !!currentJobId}
        >
          {createJobMutation.isPending ? 'Creating...' : 'Generate'}
        </Button>
      </div>

      {/* Job Status Display */}
      {currentJobId && (
        <div className="border rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Job ID: {currentJobId}</h3>
              <p className="text-sm text-muted-foreground">
                Status: {jobStatus?.status || 'queued'}
              </p>
            </div>
            
            {/* Status Badge */}
            <StatusBadge status={jobStatus?.status} />
          </div>

          {/* Progress Bar */}
          {jobStatus?.progress && (
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${jobStatus.progress}%` }}
              />
            </div>
          )}

          {/* Error Display */}
          {jobStatus?.status === 'failed' && (
            <div className="bg-destructive/10 border border-destructive rounded p-4">
              <p className="text-destructive font-medium">Generation Failed</p>
              <p className="text-sm text-muted-foreground">{jobStatus.error}</p>
            </div>
          )}

          {/* Video Player */}
          {jobStatus?.status === 'completed' && videoData && (
            <div className="space-y-4">
              <h3 className="font-semibold">Generated Video</h3>
              <VideoPlayer src={videoData.final_video} />
              
              {/* Download Button */}
              <Button asChild>
                <a href={videoData.final_video} download>
                  Download Video
                </a>
              </Button>

              {/* Scene Breakdown */}
              <details className="border rounded p-4">
                <summary className="cursor-pointer font-medium">
                  Scene Breakdown ({videoData.scene_videos.length} scenes)
                </summary>
                <div className="mt-4 space-y-2">
                  {videoData.scene_videos.map((scene) => (
                    <div key={scene.scene} className="flex items-center gap-2">
                      <span className="text-sm">Scene {scene.scene}</span>
                      
                        href={scene.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary text-sm underline"
                      >
                        View
                      </a>
                    </div>
                  ))}
                </div>
              </details>

              {/* Reset Button */}
              <Button
                variant="outline"
                onClick={() => {
                  setCurrentJobId(null);
                  setTopic('');
                }}
              >
                Create Another Video
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }: { status?: string }) {
  const variants = {
    queued: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${variants[status as keyof typeof variants] || ''}`}>
      {status || 'Unknown'}
    </span>
  );
}
Video Player Component:
typescript// frontend/src/components/VideoPlayer.tsx
interface VideoPlayerProps {
  src: string;
}

export function VideoPlayer({ src }: VideoPlayerProps) {
  return (
    <div className="aspect-[9/16] max-w-sm mx-auto bg-black rounded-lg overflow-hidden">
      <video
        src={src}
        controls
        className="w-full h-full"
        preload="metadata"
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
}
Test:
bash# 1. Start backend
uvicorn app.api.main:app --reload

# 2. Start frontend
npm run dev

# 3. Go to /create
# 4. Enter topic: "Why coffee makes you productive"
# 5. Click Generate
# 6. Watch status update from queued → running → completed
# 7. See video player appear with downloadable video
Deliverable: Fully functional video creation flow with real-time updates

Day 3: Connect Analytics Dashboard to Real Data
Tasks:

Create analytics endpoints in backend
Connect frontend analytics page to real metrics
Add charts for performance visualization

Backend Code:
python# app/api/routes.py

@app.get("/v1/analytics/overview")
async def get_analytics_overview():
    """Get high-level analytics metrics"""
    
    # Query database for metrics
    total_videos = await db.fetch_val("SELECT COUNT(*) FROM jobs WHERE status = 'completed'")
    
    avg_duration = await db.fetch_val(
        "SELECT AVG(duration_seconds) FROM video_metadata WHERE created_at > NOW() - INTERVAL '30 days'"
    )
    
    total_views = await db.fetch_val(
        "SELECT SUM(views) FROM video_performance WHERE created_at > NOW() - INTERVAL '30 days'"
    ) or 0
    
    avg_retention = await db.fetch_val(
        "SELECT AVG(retention_30s) FROM video_performance WHERE created_at > NOW() - INTERVAL '30 days'"
    ) or 0
    
    return {
        "total_videos": total_videos or 0,
        "avg_duration": round(avg_duration or 0, 1),
        "total_views": total_views,
        "avg_retention": round(avg_retention * 100, 1),  # Convert to percentage
        "period": "last_30_days"
    }

@app.get("/v1/analytics/top-videos")
async def get_top_videos(limit: int = 10):
    """Get top performing videos"""
    
    videos = await db.fetch_all("""
        SELECT 
            j.id,
            j.created_at,
            mo.public_url as video_url,
            vp.views,
            vp.retention_30s,
            vp.engagement_rate
        FROM jobs j
        LEFT JOIN media_outputs mo ON j.id = mo.job_id AND mo.file_type = 'final_video'
        LEFT JOIN video_performance vp ON j.id = vp.job_id
        WHERE j.status = 'completed'
        ORDER BY vp.views DESC NULLS LAST
        LIMIT $1
    """, limit)
    
    return {
        "videos": [
            {
                "id": str(v['id']),
                "created_at": v['created_at'].isoformat(),
                "video_url": v['video_url'],
                "views": v['views'] or 0,
                "retention": round((v['retention_30s'] or 0) * 100, 1),
                "engagement": round((v['engagement_rate'] or 0) * 100, 1)
            }
            for v in videos
        ]
    }

@app.get("/v1/analytics/performance-trend")
async def get_performance_trend(days: int = 30):
    """Get daily performance metrics"""
    
    data = await db.fetch_all("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as videos_created,
            COALESCE(SUM(views), 0) as total_views,
            COALESCE(AVG(retention_30s), 0) as avg_retention
        FROM video_performance
        WHERE created_at > NOW() - INTERVAL '{days} days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """.format(days=days))
    
    return {
        "trend": [
            {
                "date": row['date'].isoformat(),
                "videos": row['videos_created'],
                "views": row['total_views'],
                "retention": round(row['avg_retention'] * 100, 1)
            }
            for row in data
        ]
    }
Frontend Code:
typescript// frontend/src/lib/api-client.ts (add these methods)
export class ApiClient {
  // ... existing methods ...

  async getAnalyticsOverview() {
    return this.request<AnalyticsOverview>('/v1/analytics/overview');
  }

  async getTopVideos(limit = 10) {
    return this.request<{ videos: TopVideo[] }>(`/v1/analytics/top-videos?limit=${limit}`);
  }

  async getPerformanceTrend(days = 30) {
    return this.request<{ trend: TrendData[] }>(`/v1/analytics/performance-trend?days=${days}`);
  }
}

interface AnalyticsOverview {
  total_videos: number;
  avg_duration: number;
  total_views: number;
  avg_retention: number;
  period: string;
}

interface TopVideo {
  id: string;
  created_at: string;
  video_url: string;
  views: number;
  retention: number;
  engagement: number;
}

interface TrendData {
  date: string;
  videos: number;
  views: number;
  retention: number;
}
Update Analytics Page:
typescript// frontend/src/pages/Analytics.tsx
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Video, Eye, Clock } from 'lucide-react';

export function Analytics() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => apiClient.getAnalyticsOverview(),
  });

  const { data: topVideos } = useQuery({
    queryKey: ['top-videos'],
    queryFn: () => apiClient.getTopVideos(10),
  });

  const { data: trendData } = useQuery({
    queryKey: ['performance-trend'],
    queryFn: () => apiClient.getPerformanceTrend(30),
  });

  if (overviewLoading) {
    return <div>Loading analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total Videos"
          value={overview?.total_videos || 0}
          icon={Video}
        />
        <StatCard
          title="Total Views"
          value={overview?.total_views.toLocaleString() || 0}
          icon={Eye}
        />
        <StatCard
          title="Avg Retention"
          value={`${overview?.avg_retention || 0}%`}
          icon={TrendingUp}
        />
        <StatCard
          title="Avg Duration"
          value={`${overview?.avg_duration || 0}s`}
          icon={Clock}
        />
      </div>

      {/* Performance Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trend (Last 30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData?.trend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="views"
                stroke="#8884d8"
                name="Views"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="retention"
                stroke="#82ca9d"
                name="Retention %"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Videos Table */}
      <Card>
        <CardHeader>
          <CardTitle>Top Performing Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {topVideos?.videos.map((video) => (
              <div
                key={video.id}
                className="flex items-center justify-between p-3 border rounded hover:bg-accent"
              >
                <div className="flex items-center gap-3">
                  <video
                    src={video.video_url}
                    className="w-16 h-28 object-cover rounded"
                    muted
                  />
                  <div>
                    <p className="text-sm font-medium">
                      {new Date(video.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      ID: {video.id.slice(0, 8)}...
                    </p>
                  </div>
                </div>
                <div className="flex gap-6 text-sm">
                  <div>
                    <p className="text-muted-foreground">Views</p>
                    <p className="font-semibold">{video.views.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Retention</p>
                    <p className="font-semibold">{video.retention}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Engagement</p>
                    <p className="font-semibold">{video.engagement}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ title, value, icon: Icon }: any) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}
Test:
bash# Seed some test data first
# Then visit /analytics to see:
# - Real video counts
# - Performance charts
# - Top videos list
Deliverable: Live analytics dashboard with real backend data

Day 4: Deploy Backend to Railway/Render
Tasks:

Dockerize backend application
Deploy to Railway with PostgreSQL
Configure environment variables

Dockerfile:
dockerfile# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
Railway Setup:
bash# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL
railway add --plugin postgresql

# 5. Deploy
railway up
Environment Variables (Railway Dashboard):
envDATABASE_URL=postgresql://...  # Auto-set by Railway
R2_ACCESS_KEY=your_key
R2_SECRET_KEY=your_secret
R2_ENDPOINT=https://...
R2_BUCKET=story-genius-videos
GEMINI_API_KEY=your_key
Production Settings:
python# app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    ENVIRONMENT: str = "production"
    
    # Use Railway's DATABASE_URL directly
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
Health Check Endpoint:
python# app/api/routes.py
@app.get("/health")
async def health_check():
    """Health check for Railway/monitoring"""
    try:
        # Test database connection
        await db.fetch_val("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }
Deploy:
bashrailway up
# Railway will:
# 1. Build Docker image
# 2. Run migrations (if configured)
# 3. Start the app
# 4. Give you a URL: https://your-app.railway.app
Verify Deployment:
bash# Test health endpoint
curl https://your-app.railway.app/health

# Test CORS
curl -H "Origin: https://yourdomain.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS https://your-app.railway.app/v1/shorts/generate
Deliverable: Backend running on Railway with PostgreSQL

Day 5: Deploy Frontend to Vercel
Tasks:

Configure production environment variables
Deploy to Vercel
Connect to deployed backend

Vercel Setup:
bash# 1. Install Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy from frontend directory
cd frontend
vercel
Environment Variables (Vercel Dashboard):
envVITE_API_BASE_URL=https://your-app.railway.app
Build Configuration (vercel.json):
json{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
Production API Client Update:
typescript// frontend/src/lib/api-client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Add retry logic for production
export class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 3
  ): Promise<T> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.request(endpoint, options, retries - 1);
      }
      throw error;
    }
  }
}
Deploy:
bashvercel --prod
# Vercel will:
# 1. Build your React app
# 2. Deploy to CDN
# 3. Give you URL: https://your-project.vercel.app
Verify:

Visit https://your-project.vercel.app
Go to /create
Generate a video
Confirm it calls Railway backend
Confirm video plays from R2

Deliverable: Full-stack app deployed and accessible

Day 6: Add Error Handling & Loading States
Tasks:

Add global error boundary
Improve loading states
Add toast notifications for user feedback

Install Dependencies:
bashnpm install sonner  # Toast notifications
Error Boundary:
typescript// frontend/src/components/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-4">
            <h2 className="text-2xl font-bold">Something went wrong</h2>
            <p className="text-muted-foreground">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <Button onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
Toast Provider:
typescript// frontend/src/App.tsx
import { Toaster } from 'sonner';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* ... routes ... */}
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
Update Create Page with Toasts:
typescript// frontend/src/pages/Create.tsx
import { toast } from 'sonner';

export function Create() {
  const createJobMutation = useMutation({
    mutationFn: (data: { topic: string }) => 
      apiClient.createJob({
        platform: 'youtube_shorts',
        audience: 'general_adult',
        topic: data.topic,
      }),
    onSuccess: (response) => {
      toast.success('VideoContinue6:41 PMgeneration started!');
setCurrentJobId(response.job_id);
},
onError: (error) => {
toast.error('Failed to create job', {
description: error.message,
});
},
});
// Watch for job completion
useEffect(() => {
if (jobStatus?.status === 'completed') {
toast.success('Video generated successfully!');
} else if (jobStatus?.status === 'failed') {
toast.error('Video generation failed', {
description: jobStatus.error,
});
}
}, [jobStatus?.status]);
// ... rest of component
}

**Loading States:**
```typescript
// frontend/src/components/LoadingSpinner.tsx
export function LoadingSpinner({ size = 'default' }: { size?: 'sm' | 'default' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="flex items-center justify-center">
      <div className={`animate-spin rounded-full border-4 border-primary border-t-transparent ${sizeClasses[size]}`} />
    </div>
  );
}

// Usage in pages
if (isLoading) return <LoadingSpinner size="lg" />;
```

**Deliverable:** Production-ready error handling and user feedback

---

### **Day 7: End-to-End Testing & Documentation**

**Tasks:**
1. Test complete user journey
2. Document deployment process
3. Create user guide

**E2E Test Checklist:**
```markdown
## Production Test Checklist

### Frontend
- [ ] Loads at https://your-project.vercel.app
- [ ] All pages render without errors
- [ ] Navigation works
- [ ] Responsive on mobile

### Backend
- [ ] Health check returns 200
- [ ] CORS works from frontend domain
- [ ] API endpoints respond correctly

### Video Creation Flow
- [ ] Enter topic → job created
- [ ] Status updates in real-time
- [ ] Video player loads when complete
- [ ] Download button works
- [ ] Video streams from R2

### Error Handling
- [ ] Invalid input shows error
- [ ] Network errors show toast
- [ ] Failed jobs display error message
- [ ] Page reload recovers state

### Performance
- [ ] Initial load < 3s
- [ ] API response < 500ms
- [ ] Video generation < 60s
- [ ] No console errors
```

**Documentation:**
```markdown
# Story Genius - Deployment Guide

## Architecture
```
Frontend (Vercel)
    ↓
Backend API (Railway)
    ↓
PostgreSQL (Railway)
    ↓
R2 Storage (Cloudflare)
URLs

Frontend: https://story-genius.vercel.app
Backend: https://story-genius.railway.app
Health: https://story-genius.railway.app/health

Environment Variables
Backend (Railway)
envDATABASE_URL=postgresql://...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
GEMINI_API_KEY=...
Frontend (Vercel)
envVITE_API_BASE_URL=https://story-genius.railway.app
Deployment Process
Backend
bashgit push main
# Railway auto-deploys
Frontend
bashgit push main
# Vercel auto-deploys
```

## Monitoring
- Railway logs: `railway logs`
- Vercel logs: Check Vercel dashboard
- API health: `/health` endpoint
```

**User Guide:**
```markdown
# How to Generate Videos

1. **Create Account** (coming soon)
2. **Go to Create Page**
   - Enter your video topic
   - Click "Generate"
3. **Wait for Generation**
   - Status updates automatically
   - Usually takes 20-60 seconds
4. **Watch & Download**
   - Video player appears when ready
   - Click download to save locally
5. **View Analytics**
   - See performance metrics
   - Track top videos
```

**Week 20 Report Template:**
```markdown
# Week 20 Report: Production Deployment

## Summary
Deployed full-stack application to production with backend on Railway and frontend on Vercel.

## Achievements
- ✅ Backend deployed to Railway with PostgreSQL
- ✅ Frontend deployed to Vercel
- ✅ R2 storage configured
- ✅ Real-time video generation working
- ✅ Analytics dashboard live
- ✅ Error handling and loading states

## URLs
- App: https://your-project.vercel.app
- API: https://your-app.railway.app
- Docs: /docs

## Metrics (First Week)
- Jobs processed: X
- Success rate: Y%
- Avg generation time: Zs
- Uptime: 99.X%

## Next Steps (Week 21)
- User authentication
- Payment integration
- Batch generation
```

**Deliverable:** Fully deployed, documented production application

---

## **Week 20 Summary**

### **What You Built:**
✅ Connected React frontend to FastAPI backend
✅ Real-time job status updates
✅ Video player with downloadable content
✅ Live analytics dashboard
✅ Backend deployed to Railway
✅ Frontend deployed to Vercel
✅ Production error handling

### **Tech Stack:**
- **Frontend:** React + Vite + shadcn/ui (Vercel)
- **Backend:** FastAPI + PostgreSQL (Railway)
- **Storage:** Cloudflare R2
- **Monitoring:** Built-in health checks

### **URLs:**
- Frontend: `https://your-project.vercel.app`
- Backend: `https://your-app.railway.app`
- API Docs: `https://your-app.railway.app/docs`

---

## **Next Week Preview (Week 21): User Authentication & Monetization**

**Goal:** Add user accounts, credits system, and Stripe payment integration

**What You'll Build:**
- Email/password authentication
- API key management
- Credit-based usage (5 free, paid tiers)
- Stripe checkout integration
- Usage tracking per user

---

Ready to start Week 20? Let me know if you need clarification on any day!