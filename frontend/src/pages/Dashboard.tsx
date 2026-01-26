import { Outlet, NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    Video,
    Palette,
    Calendar,
    BarChart3,
    LogOut
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { logout } from '@/lib/auth'

export default function Dashboard() {
    return (
        <div className="flex h-screen bg-slate-950 text-white">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
                <div className="p-6">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Story Genius
                    </h1>
                </div>

                <nav className="flex-1 space-y-1 px-3 py-4">
                    <SidebarLink to="/dashboard" icon={<LayoutDashboard size={20} />} label="Home" end />
                    <SidebarLink to="/create" icon={<Video size={20} />} label="Create Video" />
                    <SidebarLink to="/brand" icon={<Palette size={20} />} label="Brand Kits" />
                    <SidebarLink to="/calendar" icon={<Calendar size={20} />} label="Calendar" />
                    <SidebarLink to="/analytics" icon={<BarChart3 size={20} />} label="Analytics" />
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <Button
                        variant="ghost"
                        className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-900/20"
                        onClick={logout}
                    >
                        <LogOut size={20} className="mr-2" />
                        Sign Out
                    </Button>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-auto bg-slate-950">
                <Outlet />
            </main>
        </div>
    )
}

function SidebarLink({ to, icon, label, end = false }: { to: string, icon: React.ReactNode, label: string, end?: boolean }) {
    return (
        <NavLink
            to={to}
            end={end}
            className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
            )}
        >
            {icon}
            <span>{label}</span>
        </NavLink>
    )
}
