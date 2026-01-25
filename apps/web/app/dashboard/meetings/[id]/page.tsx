export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import {
    Video,
    Calendar,
    Clock,
    Users,
    FileText,
    ArrowLeft,
    Download,
    ExternalLink,
    Copy,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserAvatar } from "@/components/ui/avatar";

interface MeetingPageProps {
    params: Promise<{ id: string }>;
}

export default async function MeetingPage({ params }: MeetingPageProps) {
    const { id } = await params;
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    const { data: meeting } = await supabase
        .from("meetings")
        .select(`
            *,
            recordings (*),
            transcriptions (
                *,
                transcription_segments (*)
            )
        `)
        .eq("id", id)
        .eq("user_id", user?.id)
        .single();

    if (!meeting) {
        notFound();
    }

    const formatDuration = (seconds: number | null) => {
        if (!seconds) return "—";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m ${secs}s`;
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return "—";
        return new Date(dateStr).toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
        });
    };

    const formatTime = (dateStr: string | null) => {
        if (!dateStr) return "";
        return new Date(dateStr).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const getStatusVariant = (status: string): "completed" | "recording" | "scheduled" | "processing" | "default" => {
        switch (status) {
            case "completed": return "completed";
            case "recording": return "recording";
            case "scheduled": return "scheduled";
            case "transcribing":
            case "processing": return "processing";
            default: return "default";
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case "completed": return "Concluída";
            case "recording": return "Gravando";
            case "scheduled": return "Agendada";
            case "transcribing": return "Transcrevendo";
            case "processing": return "Processando";
            default: return status;
        }
    };

    const recording = meeting.recordings?.[0];
    const videoUrl = recording?.storage_url || (
        recording?.storage_path && process.env.NEXT_PUBLIC_R2_URL
            ? `${process.env.NEXT_PUBLIC_R2_URL}/${recording.storage_path}`
            : null
    );

    const transcription = meeting.transcriptions?.sort((a: any, b: any) => {
        if (a.status === 'completed' && b.status !== 'completed') return -1;
        if (a.status !== 'completed' && b.status === 'completed') return 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    })?.[0];

    const segments = transcription?.transcription_segments?.sort(
        (a: any, b: any) => a.segment_index - b.segment_index
    ) || [];

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <header className="mb-6">
                <Link
                    href="/dashboard/meetings"
                    className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Reuniões
                </Link>

                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <h1 className="text-2xl font-display">{meeting.title}</h1>
                            <Badge variant={getStatusVariant(meeting.status)}>
                                {getStatusLabel(meeting.status)}
                            </Badge>
                        </div>

                        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1.5">
                                <Calendar className="h-3.5 w-3.5" />
                                {formatDate(meeting.scheduled_start)}
                            </span>
                            {meeting.scheduled_start && (
                                <span className="font-mono">
                                    {formatTime(meeting.scheduled_start)}
                                </span>
                            )}
                            {meeting.duration_seconds && (
                                <>
                                    <span className="h-1 w-1 rounded-full bg-muted-foreground" />
                                    <span className="flex items-center gap-1.5">
                                        <Clock className="h-3.5 w-3.5" />
                                        {formatDuration(meeting.duration_seconds)}
                                    </span>
                                </>
                            )}
                            {meeting.participant_count > 0 && (
                                <>
                                    <span className="h-1 w-1 rounded-full bg-muted-foreground" />
                                    <span className="flex items-center gap-1.5">
                                        <Users className="h-3.5 w-3.5" />
                                        {meeting.participant_count} participantes
                                    </span>
                                </>
                            )}
                        </div>
                    </div>

                    {meeting.meeting_url && (
                        <a href={meeting.meeting_url} target="_blank" rel="noopener noreferrer">
                            <Button variant="outline" size="sm">
                                <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                                Link
                            </Button>
                        </a>
                    )}
                </div>
            </header>

            {/* Main Content - Video + Transcription side by side */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* Video Section */}
                <section className="space-y-4">
                    <div className="rounded-lg border border-border bg-card overflow-hidden">
                        {videoUrl ? (
                            <>
                                <div className="aspect-video bg-black">
                                    <video
                                        src={videoUrl}
                                        controls
                                        className="w-full h-full"
                                        poster={recording.thumbnail_url}
                                    />
                                </div>
                                <div className="px-4 py-3 border-t border-border flex items-center justify-between">
                                    <span className="text-xs text-muted-foreground">
                                        {recording.format?.toUpperCase()} · {formatDuration(recording.duration_seconds)}
                                    </span>
                                    <a href={videoUrl} download>
                                        <Button variant="ghost" size="sm" className="h-7 text-xs">
                                            <Download className="h-3 w-3 mr-1.5" />
                                            Download
                                        </Button>
                                    </a>
                                </div>
                            </>
                        ) : (
                            <div className="aspect-video bg-muted flex items-center justify-center">
                                <div className="text-center px-4">
                                    <Video className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                                    <p className="text-sm text-muted-foreground">
                                        {meeting.status === "scheduled"
                                            ? "A gravação começará quando a reunião iniciar"
                                            : meeting.status === "recording"
                                                ? "Gravação em andamento..."
                                                : meeting.status === "processing"
                                                    ? "Processando gravação..."
                                                    : "Gravação não disponível"}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Meeting Info (collapsed on desktop) */}
                    <div className="xl:hidden rounded-lg border border-border bg-card p-4">
                        <h3 className="text-sm font-medium mb-3">Informações</h3>
                        <dl className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                                <dt className="text-muted-foreground">Plataforma</dt>
                                <dd className="font-medium capitalize">{meeting.meeting_provider?.replace("_", " ") || "—"}</dd>
                            </div>
                            {meeting.actual_start && (
                                <div>
                                    <dt className="text-muted-foreground">Início real</dt>
                                    <dd className="font-medium">{formatTime(meeting.actual_start)}</dd>
                                </div>
                            )}
                            {meeting.actual_end && (
                                <div>
                                    <dt className="text-muted-foreground">Fim</dt>
                                    <dd className="font-medium">{formatTime(meeting.actual_end)}</dd>
                                </div>
                            )}
                        </dl>
                    </div>
                </section>

                {/* Transcription Section */}
                <section className="rounded-lg border border-border bg-card flex flex-col min-h-[400px] xl:min-h-0 xl:h-[calc(100vh-220px)]">
                    <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <h2 className="text-sm font-medium">Transcrição</h2>
                        </div>
                        {transcription?.word_count && (
                            <span className="text-xs text-muted-foreground">
                                {transcription.word_count.toLocaleString()} palavras
                            </span>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {segments.length > 0 ? (
                            <div className="divide-y divide-border">
                                {segments.map((segment: any, index: number) => (
                                    <div
                                        key={segment.id || index}
                                        className="px-4 py-3 hover:bg-accent/30 transition-colors"
                                    >
                                        <div className="flex items-start gap-3">
                                            {segment.speaker_name && (
                                                <UserAvatar name={segment.speaker_name} size="sm" />
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    {segment.speaker_name && (
                                                        <span className="text-xs font-medium">
                                                            {segment.speaker_name}
                                                        </span>
                                                    )}
                                                    <span className="text-xs text-muted-foreground font-mono">
                                                        {Math.floor(segment.start_time_ms / 60000)}:{String(Math.floor((segment.start_time_ms % 60000) / 1000)).padStart(2, '0')}
                                                    </span>
                                                </div>
                                                <p className="text-sm leading-relaxed">
                                                    {segment.text}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : transcription?.full_text ? (
                            <div className="p-4">
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                    {transcription.full_text}
                                </p>
                            </div>
                        ) : transcription?.status === "processing" ? (
                            <div className="flex items-center justify-center h-full p-8">
                                <div className="text-center">
                                    <div className="h-8 w-8 rounded-lg bg-primary/10 mx-auto flex items-center justify-center mb-3 animate-pulse">
                                        <FileText className="h-4 w-4 text-primary" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Transcrição em andamento...
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full p-8">
                                <div className="text-center">
                                    <FileText className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                                    <p className="text-sm text-muted-foreground">
                                        {meeting.status === "scheduled"
                                            ? "A transcrição será gerada após a reunião"
                                            : "Transcrição não disponível"}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Transcription footer with copy action */}
                    {transcription?.full_text && (
                        <div className="px-4 py-3 border-t border-border flex-shrink-0">
                            <Button variant="ghost" size="sm" className="h-7 text-xs w-full">
                                <Copy className="h-3 w-3 mr-1.5" />
                                Copiar transcrição
                            </Button>
                        </div>
                    )}
                </section>
            </div>

            {/* Participants - Only if there are participants */}
            {meeting.participants && Array.isArray(meeting.participants) && meeting.participants.length > 0 && (
                <section className="mt-6 rounded-lg border border-border bg-card p-4">
                    <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        Participantes
                    </h3>
                    <div className="flex flex-wrap gap-2">
                        {meeting.participants.map((participant: string, i: number) => (
                            <div
                                key={i}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted text-sm"
                            >
                                <UserAvatar name={participant} size="xs" />
                                <span>{participant}</span>
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}
