# Week 19 Plan: Creator Dashboard (Frontend Reality)

**Theme:** Make everything you built in Week 18 **visible and clickable**

---

## Current State
- ✅ Week 18: All backend APIs work (preview, editor, brand kit, calendar, analytics)
- ❌ **Problem:** Creators can't use it without knowing Python/API calls
- ✅ **Solution:** Build a web dashboard they can actually use

---

## Week 19 Architecture Decision

**Stack:**
- **Frontend:** React + Vite (faster than Next.js for dashboard)
- **UI Library:** shadcn/ui + Tailwind (professional, copy-paste components)
- **State:** React Query (handles API caching automatically)
- **Routing:** React Router v6
- **Deployment:** Vercel (free tier, auto-deploy from GitHub)

**Why NOT Next.js:** 
- You're building a dashboard, not a marketing site
- Vite is 10x faster for development
- Less complexity (no SSR overhead)

---

## Day-by-Day Plan

### Day 1 (Monday) - Project Setup + Login Screen
**Goal:** Get the shell running with auth

**Implementation:**
```bash
# Create frontend project
cd C:\Users\kumar\Desktop\WorkSpace\yt-video-creator
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Install dependencies
npm install @tanstack/react-query axios
npm install -D tailwindcss postcss autoprefixer
npm install react-router-dom lucide-react

# Setup shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input label
```

**File Structure:**
```
frontend/
├── src/
│   ├── components/
│   │   └── ui/           # shadcn components
│   ├── pages/
│   │   ├── Login.tsx
│   │   └── Dashboard.tsx
│   ├── lib/
│   │   ├── api.ts        # Axios instance
│   │   └── auth.ts       # Auth helpers
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Login Page (`src/pages/Login.tsx`):**
```tsx
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleLogin = async () => {
    // TODO: Call backend /auth/login
    // For now, just store mock token
    localStorage.setItem('token', 'mock-token-123')
    window.location.href = '/dashboard'
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <Card className="w-96 p-6">
        <h1 className="text-2xl font-bold mb-6">Story Genius</h1>
        <Input 
          placeholder="Email" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4"
        />
        <Input 
          type="password"
          placeholder="Password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
        />
        <Button onClick={handleLogin} className="w-full">
          Sign In
        </Button>
      </Card>
    </div>
  )
}
```

**Test:** `npm run dev` → see login page at `localhost:5173`

---

### Day 2 (Tuesday) - Dashboard Layout + Navigation
**Goal:** Build the main shell with sidebar navigation

**Implementation:**
```tsx
// src/pages/Dashboard.tsx
import { Outlet } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Video, 
  Palette, 
  Calendar, 
  BarChart3 
} from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="flex h-screen bg-slate-950 text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800">
        <div className="p-6">
          <h1 className="text-xl font-bold">Story Genius</h1>
        </div>
        <nav className="space-y-1 px-3">
          <NavLink icon={<LayoutDashboard />} href="/dashboard" label="Home" />
          <NavLink icon={<Video />} href="/create" label="Create Video" />
          <NavLink icon={<Palette />} href="/brand" label="Brand Kits" />
          <NavLink icon={<Calendar />} href="/calendar" label="Calendar" />
          <NavLink icon={<BarChart3 />} href="/analytics" label="Analytics" />
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ icon, href, label }) {
  return (
    <a 
      href={href}
      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-800"
    >
      {icon}
      <span>{label}</span>
    </a>
  )
}
```

**Routes (`src/App.tsx`):**
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CreateVideo from './pages/CreateVideo'
import BrandKits from './pages/BrandKits'
import ContentCalendar from './pages/ContentCalendar'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />}>
          <Route index element={<Navigate to="/create" replace />} />
          <Route path="/create" element={<CreateVideo />} />
          <Route path="/brand" element={<BrandKits />} />
          <Route path="/calendar" element={<ContentCalendar />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

**Test:** Navigate between pages, sidebar highlights active page

---

### Day 3 (Wednesday) - Create Video Flow (Preview Screen)
**Goal:** The main creation screen with preview generation

**Implementation:**
```tsx
// src/pages/CreateVideo.tsx
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { api } from '@/lib/api'

export default function CreateVideo() {
  const [idea, setIdea] = useState('')
  const [preview, setPreview] = useState(null)

  const generatePreview = useMutation({
    mutationFn: async (idea: string) => {
      const response = await api.post('/v1/preview', { 
        topic: idea,
        audience_baseline: 'general_adult',
        tone: 'neutral'
      })
      return response.data
    },
    onSuccess: (data) => setPreview(data)
  })

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Create Video</h1>

      {/* Input Section */}
      <div className="mb-6">
        <label className="block mb-2 font-medium">Video Idea</label>
        <Textarea 
          placeholder="E.g., Why coffee makes you productive"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          className="min-h-32"
        />
        <Button 
          onClick={() => generatePreview.mutate(idea)}
          disabled={!idea || generatePreview.isPending}
          className="mt-4"
        >
          {generatePreview.isPending ? 'Generating...' : 'Generate Preview'}
        </Button>
      </div>

      {/* Preview Section */}
      {preview && (
        <div className="bg-slate-900 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Preview</h2>
          
          {/* Metrics */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <MetricCard label="Duration" value={`${preview.estimated_duration}s`} />
            <MetricCard label="Cost" value={`$${preview.estimated_cost}`} />
            <MetricCard label="Hook Score" value={`${preview.hook_score}%`} />
          </div>

          {/* Script */}
          <div className="space-y-4">
            {preview.scenes.map((scene, idx) => (
              <SceneCard key={idx} scene={scene} index={idx} />
            ))}
          </div>

          <Button className="w-full mt-6" size="lg">
            Generate Full Video
          </Button>
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-slate-800 rounded p-4 text-center">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  )
}

function SceneCard({ scene, index }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs bg-slate-700 px-2 py-1 rounded">
          Scene {index + 1}
        </span>
        <span className="text-xs text-slate-400">{scene.duration}s</span>
      </div>
      <p className="text-sm text-slate-300">{scene.narration}</p>
      <p className="text-xs text-slate-500 mt-2">{scene.visual_description}</p>
    </div>
  )
}
```

**API Setup (`src/lib/api.ts`):**
```ts
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
})

// Add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**Test:** Type idea → click "Generate Preview" → see preview with scenes

---

### Day 4 (Thursday) - Script Editor (Inline Editing)
**Goal:** Let users edit scene text directly in the preview

**Implementation:**
```tsx
// Add to CreateVideo.tsx
function SceneCard({ scene, index, onEdit }) {
  const [isEditing, setIsEditing] = useState(false)
  const [text, setText] = useState(scene.narration)

  const saveEdit = () => {
    onEdit(index, text)
    setIsEditing(false)
  }

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs bg-slate-700 px-2 py-1 rounded">
            Scene {index + 1}
          </span>
          <span className="text-xs text-slate-400">{scene.duration}s</span>
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => setIsEditing(!isEditing)}
        >
          {isEditing ? 'Cancel' : 'Edit'}
        </Button>
      </div>

      {isEditing ? (
        <div>
          <Textarea 
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="mb-2"
          />
          <Button size="sm" onClick={saveEdit}>Save</Button>
        </div>
      ) : (
        <p className="text-sm text-slate-300">{scene.narration}</p>
      )}

      <p className="text-xs text-slate-500 mt-2">{scene.visual_description}</p>
    </div>
  )
}
```

**Connect to backend:**
```tsx
const editScene = useMutation({
  mutationFn: async ({ jobId, sceneIdx, newText }) => {
    await api.put(`/v1/edit/${jobId}/scene/${sceneIdx}`, {
      narration: newText
    })
  }
})

const handleSceneEdit = (index, newText) => {
  editScene.mutate({
    jobId: preview.job_id,
    sceneIdx: index,
    newText
  })
  // Update local state
  const updatedScenes = [...preview.scenes]
  updatedScenes[index].narration = newText
  setPreview({ ...preview, scenes: updatedScenes })
}
```

**Test:** Click "Edit" on a scene → change text → save → see update

---

### Day 5 (Friday) - Brand Kits Manager
**Goal:** Create and manage brand kits (visual style, voice, colors)

**Implementation:**
```tsx
// src/pages/BrandKits.tsx
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Plus } from 'lucide-react'

export default function BrandKits() {
  const { data: kits } = useQuery({
    queryKey: ['brandKits'],
    queryFn: async () => {
      const response = await api.get('/v1/branding/kits')
      return response.data
    }
  })

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Brand Kits</h1>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Kit
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {kits?.map((kit) => (
          <BrandKitCard key={kit.id} kit={kit} />
        ))}
      </div>
    </div>
  )
}

function BrandKitCard({ kit }) {
  return (
    <Card className="p-6 bg-slate-900 hover:bg-slate-800 cursor-pointer">
      <h3 className="font-bold mb-4">{kit.name}</h3>
      <div className="space-y-2 text-sm text-slate-400">
        <div>Style: {kit.visual_style}</div>
        <div>Voice: {kit.voice_preference}</div>
        <div className="flex gap-2">
          {kit.color_palette.map((color) => (
            <div 
              key={color}
              className="w-6 h-6 rounded-full"
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>
    </Card>
  )
}
```

**Test:** See list of brand kits, click to edit (Day 6 will add create/edit dialog)

---

### Day 6 (Saturday) - Content Calendar View
**Goal:** Visual calendar showing scheduled videos

**Implementation:**
```tsx
// src/pages/ContentCalendar.tsx
import { useQuery } from '@tanstack/react-query'
import { Calendar } from '@/components/ui/calendar'
import { Card } from '@/components/ui/card'

export default function ContentCalendar() {
  const { data: slots } = useQuery({
    queryKey: ['calendarSlots'],
    queryFn: async () => {
      const response = await api.get('/v1/calendar/slots')
      return response.data
    }
  })

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Content Calendar</h1>

      <div className="grid grid-cols-2 gap-8">
        {/* Calendar Widget */}
        <Card className="p-6">
          <Calendar 
            mode="multiple"
            selected={slots?.map(s => new Date(s.slot_date))}
          />
        </Card>

        {/* Upcoming Slots */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Upcoming Videos</h2>
          {slots?.slice(0, 5).map((slot) => (
            <SlotCard key={slot.id} slot={slot} />
          ))}
        </div>
      </div>
    </div>
  )
}

function SlotCard({ slot }) {
  return (
    <Card className="p-4 bg-slate-900">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{slot.theme}</div>
          <div className="text-sm text-slate-400">
            {new Date(slot.slot_date).toLocaleDateString()}
          </div>
        </div>
        <div className={`px-2 py-1 rounded text-xs ${
          slot.status === 'generated' ? 'bg-green-900 text-green-300' :
          slot.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
          'bg-slate-700 text-slate-300'
        }`}>
          {slot.status}
        </div>
      </div>
    </Card>
  )
}
```

**Test:** See calendar with marked dates, list of upcoming videos

---

### Day 7 (Sunday) - Analytics Dashboard + Integration Test
**Goal:** Show performance metrics and verify everything works together

**Implementation:**
```tsx
// src/pages/Analytics.tsx
import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/ui/card'
import { BarChart3, TrendingUp, Eye, Clock } from 'lucide-react'

export default function Analytics() {
  const { data: stats } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await api.get('/v1/analytics/overview')
      return response.data
    }
  })

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Analytics</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <StatCard 
          icon={<Eye />}
          label="Total Views"
          value={stats?.total_views || 0}
        />
        <StatCard 
          icon={<Clock />}
          label="Avg Retention"
          value={`${stats?.avg_retention || 0}%`}
        />
        <StatCard 
          icon={<TrendingUp />}
          label="Videos Created"
          value={stats?.total_videos || 0}
        />
        <StatCard 
          icon={<BarChart3 />}
          label="Best Hook Type"
          value={stats?.best_hook || 'N/A'}
        />
      </div>

      {/* Top Performers */}
      <Card className="p-6 bg-slate-900">
        <h2 className="text-xl font-bold mb-4">Top Performing Videos</h2>
        <div className="space-y-4">
          {stats?.top_videos?.map((video) => (
            <VideoRow key={video.id} video={video} />
          ))}
        </div>
      </Card>
    </div>
  )
}

function StatCard({ icon, label, value }) {
  return (
    <Card className="p-6 bg-slate-900">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-slate-800 rounded-lg">
          {icon}
        </div>
        <div>
          <div className="text-sm text-slate-400">{label}</div>
          <div className="text-2xl font-bold">{value}</div>
        </div>
      </div>
    </Card>
  )
}
```

**Integration Test:**
```tsx
// src/tests/frontend-e2e.test.ts
describe('Creator Workflow', () => {
  it('should complete full creation flow', async () => {
    // 1. Login
    await page.goto('http://localhost:5173')
    await page.fill('input[type=email]', 'test@example.com')
    await page.fill('input[type=password]', 'password')
    await page.click('button:has-text("Sign In")')

    // 2. Create video preview
    await page.click('a:has-text("Create Video")')
    await page.fill('textarea', 'Why space is cold')
    await page.click('button:has-text("Generate Preview")')
    await page.waitForSelector('text=Preview')

    // 3. Edit scene
    await page.click('button:has-text("Edit")').first()
    await page.fill('textarea', 'Updated hook text')
    await page.click('button:has-text("Save")')

    // 4. Generate video
    await page.click('button:has-text("Generate Full Video")')
    await expect(page.locator('text=Generating')).toBeVisible()
  })
})
```

---

## Week 19 Deliverables

**Files Created:**
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── CreateVideo.tsx
│   │   ├── BrandKits.tsx
│   │   ├── ContentCalendar.tsx
│   │   └── Analytics.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── auth.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Backend Changes:**
```python
# Add CORS to FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Success Metrics

| Feature | Target |
|---------|--------|
| Login → Dashboard | <2 seconds |
| Generate Preview | <5 seconds |
| Edit Scene | Instant (optimistic update) |
| Brand Kit Creation | <10 seconds |
| Calendar Load | <3 seconds |
| Analytics Load | <2 seconds |

---

## Deployment (End of Week)

```bash
# Frontend
cd frontend
npm run build
vercel --prod

# Backend (if needed)
# Deploy to Railway/Render/Fly.io
```

---

## Next Week Preview (Week 20)

- **Video Player:** Inline preview of generated videos
- **Batch Operations:** Select multiple calendar slots and generate all at once
- **Real-time Updates:** WebSocket for live generation progress
- **Mobile Responsive:** Make dashboard work on tablets

---

**Start Day 1 Monday. Ship working dashboard by Sunday. No feature creep.**