export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import {
    Video,
    Calendar,
    Clock,
    Users,
    FileText,
    Play,
    ArrowLeft,
    Download,
    ExternalLink
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface MeetingPageProps {
    params: Promise<{ id: string }>;
}

export default async function MeetingPage({ params }: MeetingPageProps) {
    const { id } = await params;
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    // Get meeting details
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
        if (!seconds) return "--";
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        }
        return `${minutes}m ${secs}s`;
    };

    const getStatusInfo = (status: string) => {
        switch (status) {
            case "completed":
                return { label: "Concluída", color: "bg-success/20 text-success" };
            case "recording":
                return { label: "Gravando", color: "bg-destructive/20 text-destructive animate-pulse" };
            case "scheduled":
                return { label: "Agendada", color: "bg-info/20 text-info" };
            case "transcribing":
                return { label: "Transcrevendo", color: "bg-primary/20 text-primary" };
            case "processing":
                return { label: "Processando", color: "bg-primary/20 text-primary" };
            default:
                return { label: status, color: "bg-muted text-muted-foreground" };
        }
    };

    const statusInfo = getStatusInfo(meeting.status);
    const recording = meeting.recordings?.[0];

    // Fallback logic for video URL if storage_url is missing but storage_path exists
    const videoUrl = recording?.storage_url || (
        recording?.storage_path && process.env.NEXT_PUBLIC_R2_URL
            ? `${process.env.NEXT_PUBLIC_R2_URL}/${recording.storage_path}`
            : null
    );

    // Sort transcriptions to get the most relevant one (completed first, then by date)
    const transcription = meeting.transcriptions?.sort((a: any, b: any) => {
        // Prioritize completed
        if (a.status === 'completed' && b.status !== 'completed') return -1;
        if (a.status !== 'completed' && b.status === 'completed') return 1;

        // Then by creation date (newest first)
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    })?.[0];

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Back Button */}
            <Link href="/dashboard/meetings">
                <Button variant="ghost" size="sm" className="gap-2">
                    <ArrowLeft className="h-4 w-4" />
                    Voltar para reuniões
                </Button>
            </Link>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-2">
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl sm:text-3xl font-bold">{meeting.title}</h1>
                        <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${statusInfo.color}`}>
                            {statusInfo.label}
                        </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1.5">
                            <Calendar className="h-4 w-4" />
                            {meeting.scheduled_start
                                ? new Date(meeting.scheduled_start).toLocaleDateString("pt-BR", {
                                    day: "numeric",
                                    month: "long",
                                    year: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })
                                : "Sem data agendada"}
                        </span>
                        {meeting.duration_seconds && (
                            <span className="flex items-center gap-1.5">
                                <Clock className="h-4 w-4" />
                                {formatDuration(meeting.duration_seconds)}
                            </span>
                        )}
                        {meeting.participant_count > 0 && (
                            <span className="flex items-center gap-1.5">
                                <Users className="h-4 w-4" />
                                {meeting.participant_count} participantes
                            </span>
                        )}
                    </div>
                </div>

                {meeting.meeting_url && (
                    <a href={meeting.meeting_url} target="_blank" rel="noopener noreferrer">
                        <Button variant="outline" size="sm" className="gap-2">
                            <ExternalLink className="h-4 w-4" />
                            Link da reunião
                        </Button>
                    </a>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Video Player */}
                    <Card className="border-border/50">
                        <CardContent className="p-0">
                            {videoUrl ? (
                                <div className="aspect-video bg-black rounded-t-xl overflow-hidden">
                                    <video
                                        src={videoUrl}
                                        controls
                                        className="w-full h-full"
                                        poster={recording.thumbnail_url}
                                    />
                                </div>
                            ) : (
                                <div className="aspect-video bg-secondary rounded-t-xl flex items-center justify-center">
                                    <div className="text-center">
                                        <div className="h-16 w-16 rounded-2xl bg-muted mx-auto flex items-center justify-center mb-4">
                                            <Video className="h-8 w-8 text-muted-foreground" />
                                        </div>
                                        <p className="text-muted-foreground">
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
                            {recording && (
                                <div className="p-4 flex items-center justify-between border-t border-border">
                                    <div className="text-sm text-muted-foreground">
                                        {recording.format?.toUpperCase()} • {formatDuration(recording.duration_seconds)}
                                    </div>
                                    {videoUrl && (
                                        <a href={videoUrl} download>
                                            <Button variant="ghost" size="sm" className="gap-2">
                                                <Download className="h-4 w-4" />
                                                Download
                                            </Button>
                                        </a>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Transcription */}
                    <Card className="border-border/50">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5" />
                                Transcrição
                            </CardTitle>
                            <CardDescription>
                                {transcription
                                    ? `${transcription.word_count || 0} palavras`
                                    : "Transcrição não disponível"}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {transcription?.full_text ? (
                                <div className="prose prose-invert prose-sm max-w-none">
                                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                                        {transcription.full_text}
                                    </p>
                                </div>
                            ) : transcription?.status === "processing" ? (
                                <div className="text-center py-8">
                                    <div className="h-12 w-12 rounded-xl bg-primary/20 mx-auto flex items-center justify-center mb-4 animate-pulse">
                                        <FileText className="h-6 w-6 text-primary" />
                                    </div>
                                    <p className="text-muted-foreground">Transcrição em andamento...</p>
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <div className="h-12 w-12 rounded-xl bg-muted mx-auto flex items-center justify-center mb-4">
                                        <FileText className="h-6 w-6 text-muted-foreground" />
                                    </div>
                                    <p className="text-muted-foreground">
                                        {meeting.status === "scheduled"
                                            ? "A transcrição será gerada após a reunião"
                                            : "Transcrição não disponível"}
                                    </p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Meeting Info */}
                    <Card className="border-border/50">
                        <CardHeader>
                            <CardTitle>Informações</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <p className="text-sm text-muted-foreground">Plataforma</p>
                                <p className="font-medium capitalize">{meeting.meeting_provider?.replace("_", " ") || "Não especificada"}</p>
                            </div>
                            {meeting.actual_start && (
                                <div>
                                    <p className="text-sm text-muted-foreground">Iniciou em</p>
                                    <p className="font-medium">
                                        {new Date(meeting.actual_start).toLocaleString("pt-BR")}
                                    </p>
                                </div>
                            )}
                            {meeting.actual_end && (
                                <div>
                                    <p className="text-sm text-muted-foreground">Terminou em</p>
                                    <p className="font-medium">
                                        {new Date(meeting.actual_end).toLocaleString("pt-BR")}
                                    </p>
                                </div>
                            )}
                            {meeting.bot_session_id && (
                                <div>
                                    <p className="text-sm text-muted-foreground">ID da Sessão</p>
                                    <p className="font-mono text-xs">{meeting.bot_session_id}</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Participants */}
                    {meeting.participants && Array.isArray(meeting.participants) && meeting.participants.length > 0 && (
                        <Card className="border-border/50">
                            <CardHeader>
                                <CardTitle>Participantes</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-2">
                                    {meeting.participants.map((participant: string, i: number) => (
                                        <li key={i} className="flex items-center gap-2 text-sm">
                                            <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">
                                                {participant.charAt(0).toUpperCase()}
                                            </div>
                                            {participant}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
