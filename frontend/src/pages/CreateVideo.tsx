import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent } from '@/components/ui/card'
import { VideoPlayer } from '@/components/VideoPlayer'
import { Loader2, Sparkles, AlertCircle, Download, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

export default function CreateVideo() {
    const [idea, setIdea] = useState('')
    const [currentJobId, setCurrentJobId] = useState<string | null>(null)

    // 1. Create Job Mutation
    const createJob = useMutation({
        mutationFn: async (topic: string) => {
            // Using the API client to call the backend
            return apiClient.createJob({
                platform: 'youtube_shorts',
                audience: 'general_adult',
                topic: topic,
                duration: 30,
                tone: 'neutral'
            })
        },
        onSuccess: (data) => {
            setCurrentJobId(data.job_id)
            toast.success("Job started! Generating your video...")
        },
        onError: (error) => {
            console.error("Job creation failed", error)
            toast.error("Failed to start generation")
        }
    })

    // 2. Poll Job Status
    const { data: jobStatus } = useQuery({
        queryKey: ['jobStatus', currentJobId],
        queryFn: () => apiClient.getJobStatus(currentJobId!),
        enabled: !!currentJobId,
        refetchInterval: (query) => {
            const status = query.state.data?.status
            if (status === 'completed' || status === 'failed') return false
            return 2000 // Poll every 2s
        }
    })

    // 3. Fetch Final Video when completed
    const { data: videoData } = useQuery({
        queryKey: ['jobVideo', currentJobId],
        queryFn: () => apiClient.getJobVideo(currentJobId!),
        enabled: jobStatus?.status === 'completed'
    })

    // Reset flow
    const handleReset = () => {
        setIdea('')
        setCurrentJobId(null)
    }

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">Create Video</h1>
                <p className="text-slate-400 mt-2">AI-Powered Video Generation</p>
            </div>

            {/* Input Section - Hide if job is running/done to focus on result, or keep visible to queue more (keeping simple for now) */}
            {!currentJobId ? (
                <Card className="bg-slate-900 border-slate-800 mb-8">
                    <CardContent className="pt-6">
                        <label className="block mb-2 font-medium text-slate-200">What's your video about?</label>
                        <Textarea
                            placeholder="E.g., The surprising history of the humble potato..."
                            value={idea}
                            onChange={(e) => setIdea(e.target.value)}
                            className="min-h-32 bg-slate-950 border-slate-700 text-lg"
                            disabled={createJob.isPending}
                        />
                        <div className="flex justify-end mt-4">
                            <Button
                                onClick={() => createJob.mutate(idea)}
                                disabled={!idea || createJob.isPending}
                                size="lg"
                                className="w-full sm:w-auto"
                            >
                                {createJob.isPending ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Starting...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="mr-2 h-4 w-4" />
                                        Generate Video
                                    </>
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-6">
                    {/* Status Display */}
                    <Card className="bg-slate-900 border-slate-800">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-lg">Job Status: {jobStatus?.status || 'Initiating...'}</h3>
                                {jobStatus?.status !== 'completed' && jobStatus?.status !== 'failed' && (
                                    <Loader2 className="animate-spin text-blue-400" />
                                )}
                            </div>

                            {/* Fake progress bar since we don't have real % yet usually */}
                            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${jobStatus?.status === 'completed' ? 'bg-green-500 w-full' :
                                        jobStatus?.status === 'failed' ? 'bg-red-500 w-full' :
                                            'bg-blue-500 w-1/3 animate-pulse'
                                        }`}
                                />
                            </div>

                            {jobStatus?.status === 'failed' && (
                                <div className="mt-4 p-4 bg-red-900/20 border border-red-900/50 rounded-lg text-red-300 flex items-start gap-3">
                                    <AlertCircle className="shrink-0 mt-0.5" />
                                    <div>
                                        <div className="font-bold">Generation Failed</div>
                                        <div className="text-sm opacity-80">{jobStatus.error || "Unknown error occurred"}</div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Result Display */}
                    {jobStatus?.status === 'completed' && videoData && (
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="flex flex-col items-center gap-6">
                                <div className="w-full max-w-sm">
                                    <VideoPlayer src={videoData.final_video} />
                                </div>

                                <div className="flex gap-4">
                                    <Button asChild size="lg" className="bg-green-600 hover:bg-green-700">
                                        <a href={videoData.final_video} download="story-genius-video.mp4">
                                            <Download className="mr-2 h-5 w-5" />
                                            Download Video
                                        </a>
                                    </Button>
                                    <Button variant="outline" onClick={handleReset}>
                                        <RefreshCw className="mr-2 h-5 w-5" />
                                        Create Another
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
