import React, { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
    LayoutDashboard,
    Video,
    Palette,
    Calendar,
    BarChart3,
    LogOut,
    Menu,
    X
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { logout } from '@/lib/auth'

export default function Dashboard() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
    const location = useLocation()

    // Close menu when route changes
    React.useEffect(() => {
        setIsMobileMenuOpen(false)
    }, [location.pathname])

    return (
        <div className="flex h-screen bg-slate-950 text-white">
            {/* Mobile Header */}
            <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 z-40">
                <div className="font-bold text-lg bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Story Genius
                </div>
                <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </Button>
            </div>

            {/* Mobile Overlay */}
            {isMobileMenuOpen && (
                <div
                    className="md:hidden fixed inset-0 bg-black/50 z-40"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={cn(
                "fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out md:relative md:translate-x-0 pt-16 md:pt-0",
                isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="p-6 hidden md:block">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Story Genius
                    </h1>
                </div>

                <nav className="flex-1 space-y-1 px-3 py-4">
                    <SidebarLink to="/dashboard" icon={<LayoutDashboard size={20} />} label="Home" end />
                    <SidebarLink to="/dashboard/create" icon={<Video size={20} />} label="Create Video" />
                    <SidebarLink to="/dashboard/brand" icon={<Palette size={20} />} label="Brand Kits" />
                    <SidebarLink to="/dashboard/calendar" icon={<Calendar size={20} />} label="Calendar" />
                    <SidebarLink to="/dashboard/analytics" icon={<BarChart3 size={20} />} label="Analytics" />
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
            <main className="flex-1 overflow-auto bg-slate-950 pt-16 md:pt-0 w-full">
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
