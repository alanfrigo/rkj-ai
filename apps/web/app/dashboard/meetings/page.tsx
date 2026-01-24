export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import { Video, Search, Filter, Calendar } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default async function MeetingsPage() {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    // Get all meetings
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
      created_at
    `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false });

    const formatDuration = (seconds: number | null) => {
        if (!seconds) return "--";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    };

    const getStatusInfo = (status: string) => {
        switch (status) {
            case "completed":
                return { label: "Concluída", color: "bg-success/20 text-success" };
            case "recording":
                return { label: "Gravando", color: "bg-destructive/20 text-destructive" };
            case "scheduled":
                return { label: "Agendada", color: "bg-info/20 text-info" };
            case "joining":
                return { label: "Entrando", color: "bg-warning/20 text-warning" };
            case "transcribing":
                return { label: "Transcrevendo", color: "bg-primary/20 text-primary" };
            case "processing":
                return { label: "Processando", color: "bg-primary/20 text-primary" };
            case "failed":
                return { label: "Falhou", color: "bg-destructive/20 text-destructive" };
            default:
                return { label: status, color: "bg-muted text-muted-foreground" };
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
            {meetings && meetings.length > 0 ? (
                <div className="grid gap-4">
                    {meetings.map((meeting) => {
                        const statusInfo = getStatusInfo(meeting.status);

                        return (
                            <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                                <Card className="border-border/50 hover:border-border transition-colors">
                                    <CardContent className="p-4 sm:p-6">
                                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                            <div className="flex items-start sm:items-center gap-4">
                                                <div className={`h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center ${meeting.status === "completed"
                                                    ? "bg-success/20 text-success"
                                                    : meeting.status === "recording"
                                                        ? "bg-destructive/20 text-destructive"
                                                        : "bg-info/20 text-info"
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
                                                        {meeting.participant_count && meeting.participant_count > 0 && (
                                                            <span>• {meeting.participant_count} participantes</span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-3 ml-16 sm:ml-0">
                                                <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${statusInfo.color}`}>
                                                    {statusInfo.label}
                                                </span>
                                                <span className="text-xs text-muted-foreground capitalize">
                                                    {meeting.meeting_provider?.replace("_", " ")}
                                                </span>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
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
