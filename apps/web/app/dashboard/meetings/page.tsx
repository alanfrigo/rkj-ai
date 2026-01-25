export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import { Video, Search, Filter, Calendar } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default async function MeetingsPage() {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    // Get all recorded meetings
    const { data: meetings } = await supabase
        .from("meetings")
        .select(`
      id,
      title,
      meeting_provider,
      meeting_url,
      status,
      scheduled_start,
      actual_start,
      actual_end,
      duration_seconds,
      participant_count,
      calendar_event_id,
      created_at
    `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false });

    // Get upcoming calendar events
    const { data: calendarEvents } = await supabase
        .from("calendar_events")
        .select("*")
        .eq("user_id", user?.id)
        .eq("status", "confirmed")
        .order("start_time", { ascending: true });

    // Merge and filter
    const meetingCalendarIds = new Set(meetings?.map(m => m.calendar_event_id).filter(Boolean));

    const upcomingMeetings = (calendarEvents || [])
        .filter(event => !meetingCalendarIds.has(event.id))
        .map(event => ({
            id: event.id,
            title: event.title,
            meeting_provider: event.meeting_provider,
            meeting_url: event.meeting_url,
            status: "scheduled",
            scheduled_start: event.start_time,
            actual_start: null,
            actual_end: null,
            duration_seconds: null,
            participant_count: 0,
            calendar_event_id: event.id,
            created_at: event.created_at,
            is_upcoming_event: true
        }));

    const allMeetings = [
        ...(meetings || []).map(m => ({ ...m, is_upcoming_event: false })),
        ...upcomingMeetings
    ].sort((a, b) => {
        const dateA = new Date(a.scheduled_start || a.created_at).getTime();
        const dateB = new Date(b.scheduled_start || b.created_at).getTime();
        return dateB - dateA;
    });

    const formatDuration = (seconds: number | null) => {
        if (!seconds) return "--";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    };

    const getStatusVariant = (status: string): "completed" | "recording" | "scheduled" | "processing" | "failed" | "default" => {
        switch (status) {
            case "completed": return "completed";
            case "recording": return "recording";
            case "scheduled": return "scheduled";
            case "joining":
            case "transcribing":
            case "processing": return "processing";
            case "failed": return "failed";
            default: return "default";
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case "completed": return "Concluída";
            case "recording": return "Gravando";
            case "scheduled": return "Agendada";
            case "joining": return "Entrando";
            case "transcribing": return "Transcrevendo";
            case "processing": return "Processando";
            case "failed": return "Falhou";
            default: return status;
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold">Reuniões</h1>
                    <p className="text-muted-foreground mt-1">
                        Todas as suas reuniões gravadas e agendadas
                    </p>
                </div>
            </div>

            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Buscar reuniões..."
                        className="pl-10"
                    />
                </div>
                <Button variant="outline" className="gap-2">
                    <Filter className="h-4 w-4" />
                    Filtrar
                </Button>
            </div>

            {/* Meetings List */}
            {allMeetings.length > 0 ? (
                <div className="grid gap-4">
                    {allMeetings.map((meeting) => {
                        const href = meeting.is_upcoming_event ? "#" : `/dashboard/meetings/${meeting.id}`;
                        const cardContent = (
                            <Card className={`border-border/50 transition-colors ${!meeting.is_upcoming_event ? "hover:border-border" : ""}`}>
                                <CardContent className="p-4 sm:p-6">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                        <div className="flex items-start sm:items-center gap-4">
                                            <div className={`h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center ${meeting.status === "completed"
                                                ? "bg-success/20 text-success"
                                                : meeting.status === "recording"
                                                    ? "bg-destructive/20 text-destructive"
                                                    : meeting.status === "scheduled" && meeting.meeting_url
                                                        ? "bg-info/20 text-info"
                                                        : "bg-muted text-muted-foreground"
                                                }`}>
                                                <Video className="h-6 w-6" />
                                            </div>
                                            <div className="space-y-1">
                                                <h3 className="font-semibold text-lg">{meeting.title}</h3>
                                                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                                                    <span className="flex items-center gap-1">
                                                        <Calendar className="h-4 w-4" />
                                                        {meeting.scheduled_start
                                                            ? new Date(meeting.scheduled_start).toLocaleDateString("pt-BR", {
                                                                day: "numeric",
                                                                month: "short",
                                                                year: "numeric",
                                                                hour: "2-digit",
                                                                minute: "2-digit",
                                                            })
                                                            : "Sem data"}
                                                    </span>
                                                    {meeting.duration_seconds && (
                                                        <span>• {formatDuration(meeting.duration_seconds)}</span>
                                                    )}
                                                    {meeting.participant_count > 0 && (
                                                        <span>• {meeting.participant_count} participantes</span>
                                                    )}
                                                    {meeting.is_upcoming_event && !meeting.meeting_url && (
                                                        <span className="bg-warning/10 text-warning px-1.5 py-0.5 rounded text-[10px] uppercase font-bold">Sem link</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3 ml-16 sm:ml-0">
                                            <Badge variant={getStatusVariant(meeting.status)}>
                                                {getStatusLabel(meeting.status)}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground capitalize">
                                                {meeting.meeting_provider?.replace("_", " ") || "calendário"}
                                            </span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );

                        if (meeting.is_upcoming_event) {
                            return <div key={meeting.id}>{cardContent}</div>;
                        }

                        return (
                            <Link key={meeting.id} href={href}>
                                {cardContent}
                            </Link>
                        );
                    })}
                </div>
            ) : (
                <Card className="border-border/50">
                    <CardContent className="py-16 text-center">
                        <div className="h-20 w-20 rounded-2xl bg-secondary mx-auto flex items-center justify-center mb-6">
                            <Video className="h-10 w-10 text-muted-foreground" />
                        </div>
                        <h3 className="text-xl font-semibold mb-2">Nenhuma reunião encontrada</h3>
                        <p className="text-muted-foreground max-w-sm mx-auto">
                            Quando você tiver reuniões gravadas ou agendadas, elas aparecerão aqui.
                        </p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
