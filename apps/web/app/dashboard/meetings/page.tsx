export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import { Video, Search, Clock, Users, ChevronRight } from "lucide-react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ExcludeEventButton } from "./exclude-event-button";

type MeetingWithEvent = {
    id: string;
    title: string;
    meeting_provider: string | null;
    meeting_url: string | null;
    status: string;
    scheduled_start: string | null;
    actual_start: string | null;
    actual_end: string | null;
    duration_seconds: number | null;
    participant_count: number;
    created_at: string;
    is_upcoming_event: boolean;
};

function groupMeetingsByDate(meetings: MeetingWithEvent[]) {
    const groups: { [key: string]: MeetingWithEvent[] } = {};
    const options: Intl.DateTimeFormatOptions = { timeZone: "America/Sao_Paulo" };

    const now = new Date();
    const todayStr = now.toLocaleDateString("en-CA", options);

    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toLocaleDateString("en-CA", options);

    const weekAgo = new Date(now);
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weekAgoStr = weekAgo.toLocaleDateString("en-CA", options);

    meetings.forEach((meeting) => {
        const meetingDate = new Date(meeting.scheduled_start || meeting.created_at);
        const meetingStr = meetingDate.toLocaleDateString("en-CA", options);

        let groupKey: string;
        if (meetingStr === todayStr) {
            groupKey = "Hoje";
        } else if (meetingStr === yesterdayStr) {
            groupKey = "Ontem";
        } else if (meetingStr > todayStr) {
            groupKey = "Próximos dias";
        } else if (meetingStr >= weekAgoStr) {
            groupKey = "Esta semana";
        } else {
            groupKey = meetingDate.toLocaleDateString("pt-BR", {
                month: "long",
                year: "numeric",
                timeZone: "America/Sao_Paulo"
            });
            groupKey = groupKey.charAt(0).toUpperCase() + groupKey.slice(1);
        }

        if (!groups[groupKey]) {
            groups[groupKey] = [];
        }
        groups[groupKey].push(meeting);
    });

    return groups;
}

export default async function MeetingsPage() {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

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

    const { data: calendarEvents } = await supabase
        .from("calendar_events")
        .select("*")
        .eq("user_id", user?.id)
        .eq("status", "confirmed")
        .eq("is_excluded", false)
        .order("start_time", { ascending: true });

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
            created_at: event.created_at,
            is_upcoming_event: true
        }));

    const allMeetings: MeetingWithEvent[] = [
        ...(meetings || []).map(m => ({ ...m, is_upcoming_event: false })),
        ...upcomingMeetings
    ].sort((a, b) => {
        const dateA = new Date(a.scheduled_start || a.created_at).getTime();
        const dateB = new Date(b.scheduled_start || b.created_at).getTime();
        return dateB - dateA;
    });

    const groupedMeetings = groupMeetingsByDate(allMeetings);

    const formatDuration = (seconds: number | null) => {
        if (!seconds) return "—";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    const formatTime = (dateStr: string | null) => {
        if (!dateStr) return "—";
        return new Date(dateStr).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
            timeZone: "America/Sao_Paulo",
        });
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

    const totalCount = allMeetings.length;

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <header className="mb-6">
                <div className="flex items-end justify-between gap-4 mb-4">
                    <h1 className="text-2xl font-display">Reuniões</h1>
                    <span className="text-sm text-muted-foreground">
                        {totalCount} {totalCount === 1 ? "reunião" : "reuniões"}
                    </span>
                </div>

                {/* Search */}
                <div className="relative max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Buscar reuniões..."
                        className="pl-10 text-sm"
                    />
                </div>
            </header>

            {/* Meetings List */}
            {allMeetings.length > 0 ? (
                <div className="space-y-6">
                    {Object.entries(groupedMeetings).map(([groupName, groupMeetings]) => (
                        <section key={groupName}>
                            <div className="flex items-center gap-3 mb-2">
                                <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                    {groupName}
                                </h2>
                                <div className="flex-1 h-px bg-border" />
                                <span className="text-xs text-muted-foreground">
                                    {groupMeetings.length}
                                </span>
                            </div>

                            <div className="rounded-lg border border-border bg-card overflow-hidden">
                                <table className="w-full">
                                    <thead className="sr-only">
                                        <tr>
                                            <th>Status</th>
                                            <th>Título</th>
                                            <th>Horário</th>
                                            <th>Duração</th>
                                            <th>Participantes</th>
                                            <th>Ação</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {groupMeetings.map((meeting) => {
                                            const isClickable = !meeting.is_upcoming_event;

                                            const rowContent = (
                                                <>
                                                    {/* Status */}
                                                    <td className="w-24 px-4 py-3">
                                                        <Badge
                                                            variant={getStatusVariant(meeting.status)}
                                                            className="text-[10px]"
                                                        >
                                                            {getStatusLabel(meeting.status)}
                                                        </Badge>
                                                    </td>

                                                    {/* Title + Provider */}
                                                    <td className="px-4 py-3">
                                                        <div className="flex items-center gap-3">
                                                            <div className="min-w-0 flex-1">
                                                                <p className={`text-sm font-medium truncate ${isClickable ? "group-hover:text-primary transition-colors" : ""}`}>
                                                                    {meeting.title}
                                                                </p>
                                                                <p className="text-xs text-muted-foreground capitalize">
                                                                    {meeting.meeting_provider?.replace("_", " ") || "calendário"}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </td>

                                                    {/* Time */}
                                                    <td className="w-20 px-4 py-3 hidden sm:table-cell">
                                                        <p className="text-sm font-mono text-muted-foreground">
                                                            {formatTime(meeting.scheduled_start)}
                                                        </p>
                                                    </td>

                                                    {/* Duration */}
                                                    <td className="w-20 px-4 py-3 hidden md:table-cell">
                                                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                            <Clock className="h-3 w-3" />
                                                            <span>{formatDuration(meeting.duration_seconds)}</span>
                                                        </div>
                                                    </td>

                                                    {/* Participants */}
                                                    <td className="w-20 px-4 py-3 hidden lg:table-cell">
                                                        {meeting.participant_count > 0 ? (
                                                            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                                <Users className="h-3 w-3" />
                                                                <span>{meeting.participant_count}</span>
                                                            </div>
                                                        ) : (
                                                            <span className="text-sm text-muted-foreground">—</span>
                                                        )}
                                                    </td>

                                                    {/* Arrow or Exclude Button */}
                                                    <td className="w-10 px-4 py-3 text-right">
                                                        {meeting.is_upcoming_event ? (
                                                            <ExcludeEventButton
                                                                eventId={meeting.id}
                                                                title={meeting.title}
                                                            />
                                                        ) : isClickable ? (
                                                            <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity inline-block" />
                                                        ) : null}
                                                    </td>
                                                </>
                                            );

                                            if (isClickable) {
                                                return (
                                                    <tr key={meeting.id} className="group hover:bg-accent/50 transition-colors">
                                                        <Link
                                                            href={`/dashboard/meetings/${meeting.id}`}
                                                            className="contents"
                                                        >
                                                            {rowContent}
                                                        </Link>
                                                    </tr>
                                                );
                                            }

                                            return (
                                                <tr key={meeting.id} className="group">
                                                    {rowContent}
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    ))}
                </div>
            ) : (
                <div className="rounded-lg border border-border bg-card py-16 text-center">
                    <Video className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                    <h3 className="text-lg font-medium mb-1">Nenhuma reunião</h3>
                    <p className="text-sm text-muted-foreground max-w-xs mx-auto">
                        Suas reuniões gravadas e agendadas aparecerão aqui.
                    </p>
                </div>
            )}
        </div>
    );
}
