export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import {
    Video,
    Clock,
    ArrowRight,
    CalendarDays,
    Mic,
    ChevronRight,
    Radio,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { QuickRecordPanel } from "@/components/meetings/quick-record-panel";

function formatTimeUntil(date: Date): string {
    const now = new Date();
    const diff = date.getTime() - now.getTime();

    if (diff < 0) return "agora";

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `em ${days}d`;
    if (hours > 0) return `em ${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `em ${minutes}m`;
    return "em breve";
}

function formatTime(date: Date): string {
    return date.toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
    });
}

export default async function DashboardPage() {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    const { data: profile } = await supabase
        .from("users")
        .select("full_name")
        .eq("id", user?.id)
        .single();

    const { count: totalMeetings } = await supabase
        .from("meetings")
        .select("*", { count: "exact", head: true })
        .eq("user_id", user?.id);

    const { count: completedMeetings } = await supabase
        .from("meetings")
        .select("*", { count: "exact", head: true })
        .eq("user_id", user?.id)
        .eq("status", "completed");

    const { data: recentMeetings } = await supabase
        .from("meetings")
        .select(`
            id,
            title,
            meeting_provider,
            status,
            scheduled_start,
            actual_start,
            duration_seconds,
            created_at
        `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false })
        .limit(6);

    const { data: upcomingEvents } = await supabase
        .from("calendar_events")
        .select(`
            id,
            title,
            meeting_provider,
            meeting_url,
            start_time,
            end_time,
            should_record
        `)
        .eq("user_id", user?.id)
        .eq("status", "confirmed")
        .gte("start_time", new Date().toISOString())
        .order("start_time", { ascending: true })
        .limit(5);

    const { data: calendars } = await supabase
        .from("connected_calendars")
        .select("id, calendar_name, provider, is_active")
        .eq("user_id", user?.id);

    // Check for any meeting currently recording
    const { data: recordingMeeting } = await supabase
        .from("meetings")
        .select("id, title, actual_start")
        .eq("user_id", user?.id)
        .eq("status", "recording")
        .single();

    const firstName = profile?.full_name?.split(" ")[0] || "Usuário";
    const hasCalendar = calendars && calendars.length > 0;
    const nextEvent = upcomingEvents?.[0];

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return "Bom dia";
        if (hour < 18) return "Boa tarde";
        return "Boa noite";
    };

    const formatDuration = (seconds: number | null) => {
        if (!seconds) return "";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    return (
        <div className="animate-fade-in">
            {/* Recording Alert */}
            {recordingMeeting && (
                <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-lg bg-destructive/10 border border-destructive/20">
                    <span className="status-dot status-dot-recording" />
                    <span className="text-sm font-medium">Gravando agora:</span>
                    <Link
                        href={`/dashboard/meetings/${recordingMeeting.id}`}
                        className="text-sm text-primary hover:underline"
                    >
                        {recordingMeeting.title}
                    </Link>
                </div>
            )}

            {/* Header with inline stats */}
            <header className="mb-8">
                <div className="flex items-end justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-display">
                            {getGreeting()}, {firstName}
                        </h1>
                    </div>
                    <div className="flex items-center gap-6 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                            <span className="font-mono text-lg text-foreground">{completedMeetings || 0}</span>
                            <span>gravadas</span>
                        </div>
                        <div className="h-4 w-px bg-border" />
                        <div className="flex items-center gap-2">
                            <span className="font-mono text-lg text-foreground">{totalMeetings || 0}</span>
                            <span>total</span>
                        </div>
                    </div>
                </div>

                {/* Calendar Connection Warning */}
                {!hasCalendar && (
                    <div className="flex items-center justify-between px-4 py-3 rounded-lg border border-warning/30 bg-warning/5">
                        <div className="flex items-center gap-3">
                            <CalendarDays className="h-4 w-4 text-warning" />
                            <p className="text-sm">
                                <span className="font-medium">Calendário não conectado.</span>
                                {" "}
                                <span className="text-muted-foreground">Conecte para detectar reuniões automaticamente.</span>
                            </p>
                        </div>
                        <Link href="/onboarding">
                            <Button size="sm" variant="outline">
                                Conectar
                            </Button>
                        </Link>
                    </div>
                )}
            </header>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

                {/* Left Column - Next Meeting Hero + Recent */}
                <div className="lg:col-span-3 space-y-6">

                    {/* Next Meeting Hero */}
                    {nextEvent ? (
                        <section className="relative overflow-hidden rounded-lg border border-border bg-card">
                            {/* Timeline ribbon at top */}
                            <div className="timeline-ribbon timeline-ribbon-active" />

                            <div className="p-6">
                                <div className="flex items-start justify-between gap-4 mb-4">
                                    <div className="space-y-1">
                                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                            Próxima reunião
                                        </p>
                                        <h2 className="text-xl font-display">
                                            {nextEvent.title}
                                        </h2>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-mono text-2xl font-display">
                                            {formatTime(new Date(nextEvent.start_time))}
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            {formatTimeUntil(new Date(nextEvent.start_time))}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                    <span className="capitalize">
                                        {nextEvent.meeting_provider?.replace("_", " ") || "Meet"}
                                    </span>
                                    {nextEvent.should_record && (
                                        <>
                                            <span className="h-1 w-1 rounded-full bg-muted-foreground" />
                                            <span className="flex items-center gap-1 text-primary">
                                                <Radio className="h-3 w-3" />
                                                Gravação automática
                                            </span>
                                        </>
                                    )}
                                </div>

                                {nextEvent.meeting_url && (
                                    <div className="mt-4 pt-4 border-t border-border">
                                        <a
                                            href={nextEvent.meeting_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            <Button size="sm">
                                                Entrar na reunião
                                                <ArrowRight className="h-3 w-3 ml-2" />
                                            </Button>
                                        </a>
                                    </div>
                                )}
                            </div>
                        </section>
                    ) : hasCalendar ? (
                        <section className="rounded-lg border border-border bg-card p-6 text-center">
                            <Clock className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                            <p className="text-muted-foreground">
                                Nenhuma reunião agendada
                            </p>
                        </section>
                    ) : null}

                    {/* Upcoming Events (if more than 1) */}
                    {upcomingEvents && upcomingEvents.length > 1 && (
                        <section className="rounded-lg border border-border bg-card">
                            <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                                <h3 className="text-sm font-medium">Agenda</h3>
                                <span className="text-xs text-muted-foreground">
                                    Próximos {upcomingEvents.length - 1} eventos
                                </span>
                            </div>
                            <div className="divide-y divide-border">
                                {upcomingEvents.slice(1, 4).map((event) => (
                                    <div
                                        key={event.id}
                                        className="flex items-center gap-4 px-4 py-3 hover:bg-accent/50 transition-colors"
                                    >
                                        <div className="w-14 text-center">
                                            <p className="font-mono text-sm">
                                                {formatTime(new Date(event.start_time))}
                                            </p>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{event.title}</p>
                                        </div>
                                        {event.should_record && (
                                            <Mic className="h-3 w-3 text-primary flex-shrink-0" />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Recent Meetings */}
                    <section className="rounded-lg border border-border bg-card">
                        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                            <h3 className="text-sm font-medium">Reuniões recentes</h3>
                            <Link href="/dashboard/meetings">
                                <Button variant="ghost" size="sm" className="h-7 text-xs">
                                    Ver todas
                                    <ChevronRight className="h-3 w-3 ml-1" />
                                </Button>
                            </Link>
                        </div>

                        {recentMeetings && recentMeetings.length > 0 ? (
                            <div className="divide-y divide-border">
                                {recentMeetings.map((meeting) => (
                                    <Link
                                        key={meeting.id}
                                        href={`/dashboard/meetings/${meeting.id}`}
                                        className="flex items-center gap-4 px-4 py-3 hover:bg-accent/50 transition-colors group"
                                    >
                                        <div className="w-14">
                                            <Badge
                                                variant={
                                                    meeting.status === "completed" ? "completed"
                                                    : meeting.status === "recording" ? "recording"
                                                    : meeting.status === "scheduled" ? "scheduled"
                                                    : "default"
                                                }
                                                className="w-full justify-center text-[10px]"
                                            >
                                                {meeting.status === "completed" ? "OK"
                                                    : meeting.status === "recording" ? "REC"
                                                    : meeting.status === "scheduled" ? "AGD"
                                                    : meeting.status?.slice(0, 3).toUpperCase()}
                                            </Badge>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                                                {meeting.title}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {meeting.scheduled_start
                                                    ? new Date(meeting.scheduled_start).toLocaleDateString("pt-BR", {
                                                        day: "numeric",
                                                        month: "short",
                                                    })
                                                    : "—"}
                                                {meeting.duration_seconds && (
                                                    <> · {formatDuration(meeting.duration_seconds)}</>
                                                )}
                                            </p>
                                        </div>
                                        <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="px-4 py-8 text-center">
                                <Video className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    Nenhuma reunião ainda
                                </p>
                            </div>
                        )}
                    </section>
                </div>

                {/* Right Column - Quick Record */}
                <div className="lg:col-span-2">
                    <QuickRecordPanel />
                </div>
            </div>
        </div>
    );
}
