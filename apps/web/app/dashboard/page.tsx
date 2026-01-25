export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import {
    Calendar,
    Video,
    Clock,
    ArrowRight,
    Play,
    CalendarDays,
    Mic
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { JoinMeetingCard } from "@/components/meetings/join-meeting-card";

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

    const { count: scheduledMeetings } = await supabase
        .from("calendar_events")
        .select("*", { count: "exact", head: true })
        .eq("user_id", user?.id)
        .eq("status", "confirmed")
        .gte("start_time", new Date().toISOString());

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
        .limit(5);

    const { data: upcomingEvents } = await supabase
        .from("calendar_events")
        .select(`
            id,
            title,
            meeting_provider,
            meeting_url,
            start_time,
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

    const firstName = profile?.full_name?.split(" ")[0] || "Usuário";
    const hasCalendar = calendars && calendars.length > 0;

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl text-balance">
                    Bom dia, {firstName}
                </h1>
                <p className="text-muted-foreground mt-1">
                    Aqui está o resumo das suas reuniões.
                </p>
            </div>

            {/* Calendar Connection Warning */}
            {!hasCalendar && (
                <div className="flex items-center justify-between p-4 rounded-lg border border-warning/30 bg-warning/5">
                    <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-md bg-warning/10 flex items-center justify-center">
                            <CalendarDays className="h-4 w-4 text-warning" />
                        </div>
                        <div>
                            <p className="text-sm font-medium">Calendário não conectado</p>
                            <p className="text-xs text-muted-foreground">
                                Conecte seu Google Calendar para detectar reuniões.
                            </p>
                        </div>
                    </div>
                    <Link href="/onboarding">
                        <Button size="sm">
                            Conectar
                        </Button>
                    </Link>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total de reuniões</p>
                                <p className="text-3xl font-display font-semibold mt-1">{totalMeetings || 0}</p>
                            </div>
                            <div className="h-10 w-10 rounded-md bg-primary/10 flex items-center justify-center">
                                <Video className="h-4 w-4 text-primary" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Gravadas</p>
                                <p className="text-3xl font-display font-semibold mt-1">{completedMeetings || 0}</p>
                            </div>
                            <div className="h-10 w-10 rounded-md bg-success/10 flex items-center justify-center">
                                <Play className="h-4 w-4 text-success" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Agendadas</p>
                                <p className="text-3xl font-display font-semibold mt-1">{scheduledMeetings || 0}</p>
                            </div>
                            <div className="h-10 w-10 rounded-md bg-info/10 flex items-center justify-center">
                                <Clock className="h-4 w-4 text-info" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Actions Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <JoinMeetingCard />

                <Card>
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-base font-medium">Próximas reuniões</CardTitle>
                            <Link href="/dashboard/meetings">
                                <Button variant="ghost" size="sm" className="text-xs">
                                    Ver todas
                                    <ArrowRight className="h-3 w-3 ml-1" />
                                </Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {upcomingEvents && upcomingEvents.length > 0 ? (
                            <div className="space-y-1">
                                {upcomingEvents.slice(0, 4).map((event) => (
                                    <div
                                        key={event.id}
                                        className="flex items-center gap-3 p-2.5 rounded-md hover:bg-accent transition-colors"
                                    >
                                        <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center flex-shrink-0">
                                            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{event.title}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {event.start_time
                                                    ? new Date(event.start_time).toLocaleString("pt-BR", {
                                                        day: "numeric",
                                                        month: "short",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })
                                                    : "Sem data"}
                                            </p>
                                        </div>
                                        {event.should_record && (
                                            <div className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center">
                                                <Mic className="h-2.5 w-2.5 text-primary" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <Calendar className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    Nenhuma reunião agendada
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Recent Meetings */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-base font-medium">Reuniões recentes</CardTitle>
                        <CardDescription>Últimas gravações e transcrições</CardDescription>
                    </div>
                    <Link href="/dashboard/meetings">
                        <Button variant="outline" size="sm">
                            Ver todas
                        </Button>
                    </Link>
                </CardHeader>
                <CardContent>
                    {recentMeetings && recentMeetings.length > 0 ? (
                        <div className="space-y-2">
                            {recentMeetings.map((meeting) => (
                                <Link
                                    key={meeting.id}
                                    href={`/dashboard/meetings/${meeting.id}`}
                                    className="flex items-center justify-between p-3 rounded-md hover:bg-accent transition-colors group"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`h-9 w-9 rounded-md flex items-center justify-center ${
                                            meeting.status === "completed"
                                                ? "bg-success/10"
                                                : meeting.status === "recording"
                                                    ? "bg-destructive/10"
                                                    : "bg-info/10"
                                        }`}>
                                            <Video className={`h-4 w-4 ${
                                                meeting.status === "completed"
                                                    ? "text-success"
                                                    : meeting.status === "recording"
                                                        ? "text-destructive"
                                                        : "text-info"
                                            }`} />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium">{meeting.title}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {meeting.scheduled_start
                                                    ? new Date(meeting.scheduled_start).toLocaleDateString("pt-BR", {
                                                        day: "numeric",
                                                        month: "short",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })
                                                    : "Sem data"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <Badge variant={
                                            meeting.status === "completed" ? "completed"
                                                : meeting.status === "recording" ? "recording"
                                                    : meeting.status === "scheduled" ? "scheduled"
                                                        : "default"
                                        }>
                                            {meeting.status === "completed" ? "Concluída"
                                                : meeting.status === "recording" ? "Gravando"
                                                    : meeting.status === "scheduled" ? "Agendada"
                                                        : meeting.status}
                                        </Badge>
                                        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                </Link>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <div className="h-12 w-12 rounded-lg bg-muted mx-auto flex items-center justify-center mb-3">
                                <Video className="h-5 w-5 text-muted-foreground" />
                            </div>
                            <p className="text-sm font-medium mb-1">Nenhuma reunião ainda</p>
                            <p className="text-xs text-muted-foreground">
                                {hasCalendar
                                    ? "Suas reuniões aparecerão aqui quando forem detectadas."
                                    : "Conecte seu calendário para começar a gravar."}
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
