import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'

export function HealthCheck() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['health'],
        queryFn: () => apiClient.healthCheck(),
        retry: false
    })

    if (isLoading) return <div className="flex items-center gap-2 text-slate-400 text-xs"><Loader2 className="w-3 h-3 animate-spin" /> Checking API...</div>

    if (error) return <div className="flex items-center gap-2 text-red-500 text-xs"><XCircle className="w-3 h-3" /> API Offline</div>

    return (
        <div className="flex items-center gap-2 text-green-500 text-xs">
            <CheckCircle2 className="w-3 h-3" /> API Online (v{data?.version})
        </div>
    )
}
