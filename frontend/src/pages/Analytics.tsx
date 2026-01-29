import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient, type VideoPerformance } from '@/lib/api-client'
import { BarChart3, TrendingUp, Eye, Clock, ThumbsUp, Loader2 } from 'lucide-react'

export default function Analytics() {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['analytics'],
        queryFn: async () => {
            const [overview, topVideos] = await Promise.all([
                apiClient.getAnalyticsOverview(),
                apiClient.getTopVideos()
            ])

            return {
                ...overview,
                top_videos: topVideos.videos
            }
        }
    })

    if (isLoading) {
        return (
            <div className="flex justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
            </div>
        )
    }

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent mb-8">Channel Analytics</h1>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard
                    icon={<Eye className="text-blue-400" />}
                    label="Total Views"
                    value={stats?.total_views.toLocaleString() || "0"}
                    trend="+12% vs last week"
                />
                <StatCard
                    icon={<Clock className="text-purple-400" />}
                    label="Avg Retention"
                    value={`${stats?.avg_retention}%`}
                    trend="+2% vs last week"
                />
                <StatCard
                    icon={<TrendingUp className="text-green-400" />}
                    label="Total Videos"
                    value={stats?.total_videos || "0"}
                    subtext="Keep it up!"
                />
                <StatCard
                    icon={<BarChart3 className="text-orange-400" />}
                    label="Avg Duration"
                    value={`${stats?.avg_duration}s`}
                    subtext="Optimal length"
                />
            </div>

            {/* Top Performers */}
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-xl">Top Performing Videos</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {Array.isArray(stats?.top_videos) && stats.top_videos.map((video: VideoPerformance, idx: number) => (
                            <VideoRow key={idx} video={video} index={idx} />
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function StatCard({ icon, label, value, trend, subtext }: { icon: React.ReactNode, label: string, value: string | number, trend?: string, subtext?: string }) {
    return (
        <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        {icon}
                    </div>
                    <div>
                        <div className="text-sm text-slate-400">{label}</div>
                        <div className="text-2xl font-bold text-white">{value}</div>
                    </div>
                </div>
                {(trend || subtext) && (
                    <div className={`text-xs ${trend?.includes('+') ? 'text-green-400' : 'text-slate-500'}`}>
                        {trend || subtext}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function VideoRow({ video, index }: { video: VideoPerformance, index: number }) {
    return (
        <div className="flex items-center justify-between p-4 bg-slate-950 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors">
            <div className="flex items-center gap-4">
                <div className="font-bold text-lg text-slate-600 w-6">#{index + 1}</div>
                <div>
                    <div className="font-medium text-white mb-1">{video.title}</div>
                    <div className="flex items-center gap-3 text-xs text-slate-500 uppercase tracking-wider">
                        <span>{video.platform.replace('_', ' ')}</span>
                        <span>•</span>
                        <span className="text-slate-400">{new Date().toLocaleDateString()}</span>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-6 text-sm">
                <div className="flex flex-col items-end w-20">
                    <div className="flex items-center gap-1 text-slate-300">
                        <Eye size={14} className="text-slate-500" />
                        {video.views.toLocaleString()}
                    </div>
                    <div className="text-xs text-slate-500">Views</div>
                </div>

                <div className="flex flex-col items-end w-20">
                    <div className="flex items-center gap-1 text-slate-300">
                        <Clock size={14} className="text-slate-500" />
                        {(video.avg_retention_percent * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-slate-500">Retention</div>
                </div>

                <div className="flex flex-col items-end w-16 hidden sm:flex">
                    <div className="flex items-center gap-1 text-slate-300">
                        <ThumbsUp size={14} className="text-slate-500" />
                        {video.likes.toLocaleString()}
                    </div>
                </div>
            </div>
        </div>
    )
}
