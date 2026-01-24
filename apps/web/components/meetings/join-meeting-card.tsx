"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Video, Loader2, ArrowRight, Link as LinkIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

export function JoinMeetingCard() {
    const [meetingUrl, setMeetingUrl] = useState("");
    const [title, setTitle] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const router = useRouter();

    const handleJoin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            const response = await fetch("/api/meetings/join", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    meetingUrl: meetingUrl.trim(),
                    title: title.trim() || undefined,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Falha ao iniciar gravação");
            }

            setSuccess(true);
            setMeetingUrl("");
            setTitle("");

            // Redirect to the meeting page after a short delay
            setTimeout(() => {
                router.push(`/dashboard/meetings/${data.meeting.id}`);
            }, 1500);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            setLoading(false);
        }
    };

    const isValidUrl = (url: string) => {
        const meetPattern = /^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}$/i;
        return meetPattern.test(url);
    };

    return (
        <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Video className="h-5 w-5 text-primary" />
                    Gravar Reunião Agora
                </CardTitle>
                <CardDescription>
                    Insira um link do Google Meet e o bot entrará para gravar
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleJoin} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="meetingUrl">Link do Google Meet</Label>
                        <div className="relative">
                            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="meetingUrl"
                                type="url"
                                placeholder="https://meet.google.com/xxx-xxxx-xxx"
                                className="pl-10"
                                value={meetingUrl}
                                onChange={(e) => setMeetingUrl(e.target.value)}
                                disabled={loading || success}
                                required
                            />
                        </div>
                        {meetingUrl && !isValidUrl(meetingUrl) && (
                            <p className="text-xs text-warning">
                                Formato: https://meet.google.com/abc-defg-hij
                            </p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="title">
                            Título da reunião{" "}
                            <span className="text-muted-foreground font-normal">(opcional)</span>
                        </Label>
                        <Input
                            id="title"
                            type="text"
                            placeholder="Ex: Reunião de alinhamento"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            disabled={loading || success}
                        />
                    </div>

                    {error && (
                        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="p-3 rounded-lg bg-success/10 border border-success/20 text-success text-sm">
                            ✓ Bot iniciando! Redirecionando...
                        </div>
                    )}

                    <Button
                        type="submit"
                        className="w-full"
                        disabled={loading || success || !meetingUrl || !isValidUrl(meetingUrl)}
                    >
                        {loading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : success ? (
                            "Iniciando..."
                        ) : (
                            <>
                                Iniciar Gravação
                                <ArrowRight className="h-4 w-4 ml-2" />
                            </>
                        )}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
