export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import {
    Calendar,
    Video,
    FileText,
    Clock,
    ArrowRight,
    Play,
    CalendarDays
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { JoinMeetingCard } from "@/components/meetings/join-meeting-card";

export default async function DashboardPage() {
    const supabase = await createClient();

    // Get current user
    const { data: { user } } = await supabase.auth.getUser();

    // Get user profile
    const { data: profile } = await supabase
        .from("users")
        .select("full_name")
        .eq("id", user?.id)
        .single();

    // Get stats
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
        .from("meetings")
        .select("*", { count: "exact", head: true })
        .eq("user_id", user?.id)
        .eq("status", "scheduled");

    // Get recent meetings
    const { data: recentMeetings } = await supabase
        .from("meetings")
        .select(`
      id,
      title,
      meeting_provider,
      status,
      scheduled_start,
      actual_start,
      duration_seconds
    `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false })
        .limit(5);

    // Get connected calendars
    const { data: calendars } = await supabase
        .from("connected_calendars")
        .select("id, calendar_name, provider, is_active")
        .eq("user_id", user?.id);

    const firstName = profile?.full_name?.split(" ")[0] || "Usuário";
    const hasCalendar = calendars && calendars.length > 0;

    const stats = [
        {
            label: "Total de Reuniões",
            value: totalMeetings || 0,
            icon: <Video className="h-5 w-5" />,
            color: "text-primary",
            bgColor: "bg-primary/10",
        },
        {
            label: "Gravadas",
            value: completedMeetings || 0,
            icon: <Play className="h-5 w-5" />,
            color: "text-success",
            bgColor: "bg-success/10",
        },
        {
            label: "Agendadas",
            value: scheduledMeetings || 0,
            icon: <Clock className="h-5 w-5" />,
            color: "text-info",
            bgColor: "bg-info/10",
        },
    ];

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Olá, {firstName}! 👋</h1>
                <p className="text-muted-foreground mt-1">
                    Aqui está um resumo das suas reuniões.
                </p>
            </div>

            {/* Calendar Connection Warning */}
            {!hasCalendar && (
                <Card className="border-warning/50 bg-warning/5">
                    <CardContent className="flex items-center justify-between py-4">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-warning/20 flex items-center justify-center">
                                <CalendarDays className="h-5 w-5 text-warning" />
                            </div>
                            <div>
                                <p className="font-medium">Calendário não conectado</p>
                                <p className="text-sm text-muted-foreground">
                                    Conecte seu Google Calendar para detectar reuniões automaticamente.
                                </p>
                            </div>
                        </div>
                        <Link href="/onboarding">
                            <Button size="sm">
                                Conectar
                                <ArrowRight className="h-4 w-4 ml-1" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {stats.map((stat) => (
                    <Card key={stat.label} className="border-border/50">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                                    <p className="text-3xl font-bold mt-1">{stat.value}</p>
                                </div>
                                <div className={`h-12 w-12 rounded-xl ${stat.bgColor} flex items-center justify-center ${stat.color}`}>
                                    {stat.icon}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Quick Actions Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Join Meeting Card */}
                <JoinMeetingCard />

                {/* Recent Meetings Preview */}
                <Card className="border-border/50">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-base">Próximas Reuniões</CardTitle>
                            <Link href="/meetings">
                                <Button variant="ghost" size="sm">
                                    Ver todas
                                    <ArrowRight className="h-3 w-3 ml-1" />
                                </Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {recentMeetings && recentMeetings.filter(m => m.status === "scheduled").length > 0 ? (
                            <div className="space-y-2">
                                {recentMeetings.filter(m => m.status === "scheduled").slice(0, 3).map((meeting) => (
                                    <Link
                                        key={meeting.id}
                                        href={`/meetings/${meeting.id}`}
                                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-secondary/50 transition-colors"
                                    >
                                        <div className="h-8 w-8 rounded-lg bg-info/20 flex items-center justify-center">
                                            <Clock className="h-4 w-4 text-info" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate">{meeting.title}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {meeting.scheduled_start
                                                    ? new Date(meeting.scheduled_start).toLocaleString("pt-BR", {
                                                        day: "numeric",
                                                        month: "short",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })
                                                    : "Sem data"}
                                            </p>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-6">
                                <Calendar className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    Nenhuma reunião agendada
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Recent Meetings */}
            <Card className="border-border/50">
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>Reuniões Recentes</CardTitle>
                        <CardDescription>Suas últimas reuniões gravadas e agendadas</CardDescription>
                    </div>
                    <Link href="/meetings">
                        <Button variant="outline" size="sm">
                            Ver todas
                            <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                    </Link>
                </CardHeader>
                <CardContent>
                    {recentMeetings && recentMeetings.length > 0 ? (
                        <div className="space-y-3">
                            {recentMeetings.map((meeting) => (
                                <Link
                                    key={meeting.id}
                                    href={`/meetings/${meeting.id}`}
                                    className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 hover:bg-secondary/50 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${meeting.status === "completed"
                                            ? "bg-success/20 text-success"
                                            : meeting.status === "recording"
                                                ? "bg-destructive/20 text-destructive"
                                                : "bg-info/20 text-info"
                                            }`}>
                                            <Video className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="font-medium">{meeting.title}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {meeting.scheduled_start
                                                    ? new Date(meeting.scheduled_start).toLocaleDateString("pt-BR", {
                                                        day: "numeric",
                                                        month: "short",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })
                                                    : "Sem data"
                                                }
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className={`text-xs px-2 py-1 rounded-full ${meeting.status === "completed"
                                            ? "bg-success/20 text-success"
                                            : meeting.status === "recording"
                                                ? "bg-destructive/20 text-destructive"
                                                : meeting.status === "scheduled"
                                                    ? "bg-info/20 text-info"
                                                    : "bg-muted text-muted-foreground"
                                            }`}>
                                            {meeting.status === "completed" ? "Concluída"
                                                : meeting.status === "recording" ? "Gravando"
                                                    : meeting.status === "scheduled" ? "Agendada"
                                                        : meeting.status}
                                        </span>
                                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                </Link>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <div className="h-16 w-16 rounded-2xl bg-secondary mx-auto flex items-center justify-center mb-4">
                                <Video className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <h3 className="font-medium mb-1">Nenhuma reunião ainda</h3>
                            <p className="text-sm text-muted-foreground">
                                {hasCalendar
                                    ? "Suas reuniões aparecerão aqui quando forem detectadas."
                                    : "Conecte seu calendário para começar a gravar reuniões."}
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
