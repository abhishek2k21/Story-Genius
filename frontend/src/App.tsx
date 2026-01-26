import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Pages
import Login from './pages/LoginNew'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import CreateVideo from './pages/CreateVideo'
import BrandKits from './pages/BrandKits'
import ContentCalendar from './pages/ContentCalendar'
import Analytics from './pages/Analytics'

// Create a client
const queryClient = new QueryClient()

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />

              {/* Protected routes */}
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/create" replace />} />
                <Route path="/create" element={<CreateVideo />} />
                <Route path="/brand" element={<BrandKits />} />
                <Route path="/calendar" element={<ContentCalendar />} />
                <Route path="/analytics" element={<Analytics />} />
              </Route>

              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
            <Toaster position="top-right" theme="dark" />
          </BrowserRouter>
        </QueryClientProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}
