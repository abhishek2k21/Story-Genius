import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { Plus, Palette, Mic2, Loader2 } from 'lucide-react'

interface BrandKit {
    id: string
    name: string
    visual_style: string
    color_palette: string[]
    voice_preference: string
    intro_template?: string
}

export default function BrandKits() {
    const [isCreating, setIsCreating] = useState(false)
    const [newKitName, setNewKitName] = useState('')
    const queryClient = useQueryClient()

    // 1. Fetch Kits
    const { data: kits, isLoading } = useQuery({
        queryKey: ['brandKits'],
        queryFn: async () => {
            // Mock user ID for now
            const response = await api.get('/v1/branding/kits/test_user_123')
            return response.data as BrandKit[]
        }
    })

    // 2. Create Kit Mutation
    const createKit = useMutation({
        mutationFn: async (name: string) => {
            const response = await api.post('/v1/branding/kits', null, {
                params: {
                    user_id: 'test_user_123',
                    name: name,
                    style: 'cinematic' // Default
                }
            })
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['brandKits'] })
            setIsCreating(false)
            setNewKitName('')
        }
    })

    const handleCreate = () => {
        if (!newKitName.trim()) return;
        createKit.mutate(newKitName)
    }

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-400 to-rose-500 bg-clip-text text-transparent">Brand Kits</h1>
                    <p className="text-slate-400 mt-1">Manage your channel's visual identity.</p>
                </div>

                {!isCreating ? (
                    <Button onClick={() => setIsCreating(true)} className="bg-rose-600 hover:bg-rose-700">
                        <Plus className="w-4 h-4 mr-2" />
                        New Brand Kit
                    </Button>
                ) : (
                    <div className="flex gap-2 animate-in fade-in slide-in-from-right-4 duration-300">
                        <Input
                            placeholder="Kit Name (e.g. My Tech Channel)"
                            value={newKitName}
                            onChange={(e) => setNewKitName(e.target.value)}
                            className="w-64 bg-slate-900 border-slate-700 text-white"
                            autoFocus
                        />
                        <Button onClick={handleCreate} disabled={createKit.isPending}>
                            {createKit.isPending ? <Loader2 className="animate-spin" /> : 'Save'}
                        </Button>
                        <Button variant="ghost" onClick={() => setIsCreating(false)}>Cancel</Button>
                    </div>
                )}
            </div>

            {isLoading && (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {kits?.map((kit) => (
                    <BrandKitCard key={kit.id} kit={kit} />
                ))}
                {kits?.length === 0 && !isLoading && (
                    <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-800 rounded-lg text-slate-500">
                        No brand kits found. Create one to get started!
                    </div>
                )}
            </div>
        </div>
    )
}

function BrandKitCard({ kit }: { kit: BrandKit }) {
    return (
        <Card className="bg-slate-900 border-slate-800 hover:border-slate-700 transition-all group overflow-hidden">
            <div className="h-2 bg-gradient-to-r from-rose-500 to-pink-500" />
            <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                    <h3 className="font-bold text-lg text-white group-hover:text-rose-400 transition-colors">{kit.name}</h3>
                    {/* Action menu could go here */}
                </div>

                <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm text-slate-400">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0 text-slate-500">
                            <Palette size={14} />
                        </div>
                        <div>
                            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500">Visual Style</div>
                            <div className="text-slate-300 capitalize">{kit.visual_style}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 text-sm text-slate-400">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0 text-slate-500">
                            <Mic2 size={14} />
                        </div>
                        <div>
                            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500">Voice</div>
                            <div className="text-slate-300">{kit.voice_preference.split('-')[2] || kit.voice_preference}</div>
                        </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-slate-800/50">
                        <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2">Color Palette</div>
                        <div className="flex gap-2">
                            {kit.color_palette.map((color, idx) => (
                                <div
                                    key={idx}
                                    className="w-8 h-8 rounded-full border border-white/10 shadow-sm"
                                    style={{ backgroundColor: color }}
                                    title={color}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
