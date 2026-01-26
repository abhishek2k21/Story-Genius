import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { Calendar as CalendarIcon, Video, Clock } from 'lucide-react'
import { format } from 'date-fns'

interface CalendarSlot {
    id: string
    slot_date: string
    slot_time: string
    theme: string
    topic?: string
    status: 'pending' | 'planned' | 'generated' | 'published'
}

export default function ContentCalendar() {
    const [date, setDate] = useState<Date | undefined>(new Date())

    // Fetch slots
    const { data: slots } = useQuery({
        queryKey: ['calendarSlots'],
        queryFn: async () => {
            // Mock call
            const response = await api.get('/v1/calendar/slots/test_user_123')
            // Since we don't have this exact endpoint implemented in backend yet (we did service but maybe not route),
            // we might need to mock return in api.ts or implement the route properly.
            // For now assuming it returns a list.
            return response.data as CalendarSlot[]
        },
        // Mock data for initial UI dev since backend endpoint might be missing specific "list slots" route
        initialData: [
            { id: '1', slot_date: new Date().toISOString(), slot_time: '18:00', theme: 'Motivation', status: 'pending' },
            { id: '2', slot_date: new Date(Date.now() + 86400000 * 2).toISOString(), slot_time: '18:00', theme: 'Tech Tip', status: 'planned', topic: 'How to use AI' },
            { id: '3', slot_date: new Date(Date.now() + 86400000 * 5).toISOString(), slot_time: '18:00', theme: 'Story', status: 'generated', topic: 'The first computer' },
        ] as CalendarSlot[]
    })

    // Group slots by date string for calendar markers
    const slotsByDate = slots?.reduce((acc, slot) => {
        const dateStr = new Date(slot.slot_date).toDateString()
        if (!acc[dateStr]) acc[dateStr] = []
        acc[dateStr].push(slot)
        return acc
    }, {} as Record<string, CalendarSlot[]>)

    const selectedSlots = date ? slotsByDate?.[date.toDateString()] || [] : []

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-500 bg-clip-text text-transparent">Content Calendar</h1>
                    <p className="text-slate-400 mt-1">Plan and schedule your content consistency.</p>
                </div>
                <Button variant="outline" className="border-slate-700 hover:bg-slate-800">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    Auto-Schedule Month
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Calendar Widget */}
                <div className="lg:col-span-8">
                    <Card className="bg-slate-900 border-slate-800 h-full">
                        <CardContent className="p-6 flex justify-center">
                            <Calendar
                                mode="single"
                                selected={date}
                                onSelect={setDate}
                                className="rounded-md border border-slate-800 bg-slate-950"
                                modifiers={{
                                    booked: (date) => !!slotsByDate?.[date.toDateString()]
                                }}
                                modifiersStyles={{
                                    booked: { border: '2px solid var(--primary)', borderRadius: '100%' }
                                }}
                            />
                        </CardContent>
                    </Card>
                </div>

                {/* Selected Day Details */}
                <div className="lg:col-span-4 space-y-4">
                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-lg">
                                {date ? format(date, 'EEEE, MMMM do') : 'Select a date'}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {selectedSlots.length > 0 ? (
                                selectedSlots.map(slot => (
                                    <SlotCard key={slot.id} slot={slot} />
                                ))
                            ) : (
                                <div className="text-center py-8 text-slate-500">
                                    <Clock className="mx-auto h-8 w-8 mb-2 opacity-50" />
                                    <p>No videos scheduled.</p>
                                    <Button variant="link" className="mt-2 text-blue-400">Schedule Video</Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-sm uppercase tracking-wider text-slate-500">Upcoming</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Filter out past or current selection to show upcoming */}
                            {slots?.filter(s => new Date(s.slot_date) > new Date()).slice(0, 3).map(slot => (
                                <div key={slot.id} className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-2 h-2 rounded-full ${getStatusColor(slot.status)}`} />
                                        <span className="text-slate-300">{format(new Date(slot.slot_date), 'MMM d')}</span>
                                    </div>
                                    <span className="text-slate-500 truncate max-w-[120px]">{slot.theme}</span>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}

function SlotCard({ slot }: { slot: CalendarSlot }) {
    return (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    {slot.slot_time}
                </span>
                <StatusBadge status={slot.status} />
            </div>

            <div className="font-medium text-slate-200 mb-1">{slot.theme}</div>
            {slot.topic && (
                <div className="text-sm text-slate-400 flex items-start gap-2">
                    <Video className="w-4 h-4 mt-0.5 text-blue-500 shrink-0" />
                    {slot.topic}
                </div>
            )}

            {slot.status === 'pending' && (
                <Button size="sm" variant="secondary" className="w-full mt-3 h-8 text-xs">
                    Assign Topic
                </Button>
            )}
        </div>
    )
}

function StatusBadge({ status }: { status: string }) {
    const styles = {
        pending: "bg-slate-800 text-slate-400",
        planned: "bg-blue-900/30 text-blue-400 border-blue-900",
        generated: "bg-purple-900/30 text-purple-400 border-purple-900",
        published: "bg-green-900/30 text-green-400 border-green-900"
    }

    return (
        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${styles[status as keyof typeof styles]}`}>
            {status}
        </span>
    )
}

function getStatusColor(status: string) {
    switch (status) {
        case 'generated': return 'bg-purple-500'
        case 'published': return 'bg-green-500'
        case 'planned': return 'bg-blue-500'
        default: return 'bg-slate-600'
    }
}
