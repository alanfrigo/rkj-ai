"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    Calendar,
    Check,
    ChevronRight,
    Loader2,
    Sparkles,
    Video,
    ArrowRight
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type OnboardingStep = "welcome" | "connect" | "success";

export default function OnboardingClient() {
    const [step, setStep] = useState<OnboardingStep>("welcome");
    const [fullName, setFullName] = useState("");
    const [loading, setLoading] = useState(false);
    const [connectingGoogle, setConnectingGoogle] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const supabase = createClient();

    useEffect(() => {
        // Load user's current name and check calendar status
        const initialize = async () => {
            const { data: { user } } = await supabase.auth.getUser();

            if (user?.user_metadata?.full_name) {
                setFullName(user.user_metadata.full_name);
            }

            // Check if user already has a connected calendar
            if (user) {
                const { data: calendars } = await supabase
                    .from("connected_calendars")
                    .select("id")
                    .eq("user_id", user.id)
                    .eq("is_active", true)
                    .limit(1);

                if (calendars && calendars.length > 0) {
                    // Calendar already connected, skip to success
                    setStep("success");
                    return;
                }
            }

            // Check URL params for step
            const params = new URLSearchParams(window.location.search);
            if (params.get("step") === "success") {
                setStep("success");
            }
        };

        initialize();
    }, [supabase, supabase.auth]);

    const handleWelcomeNext = async () => {
        if (!fullName.trim()) {
            setError("Por favor, insira seu nome");
            return;
        }

        setLoading(true);
        setError(null);

        // Update user's full name
        const { error } = await supabase.auth.updateUser({
            data: { full_name: fullName.trim() }
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        // Also update in public.users table
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            await supabase
                .from("users")
                .update({ full_name: fullName.trim() })
                .eq("id", user.id);
        }

        setLoading(false);
        setStep("connect");
    };

    const handleConnectGoogle = async () => {
        setConnectingGoogle(true);
        setError(null);

        // Redirect to Google Calendar OAuth with additional scopes
        const appUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;

        const { error } = await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${appUrl}/api/calendar/callback`,
                scopes: "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events.readonly",
                queryParams: {
                    access_type: "offline",
                    prompt: "consent",
                },
            },
        });

        if (error) {
            setError(error.message);
            setConnectingGoogle(false);
        }
    };

    const handleSkip = () => {
        router.push("/");
    };

    const handleGoToDashboard = () => {
        router.push("/");
    };

    const steps = [
        { id: "welcome", label: "Bem-vindo" },
        { id: "connect", label: "Calendário" },
        { id: "success", label: "Pronto" },
    ];

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Progress */}
            <div className="flex items-center justify-center gap-2">
                {steps.map((s, i) => (
                    <div key={s.id} className="flex items-center">
                        <div
                            className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${step === s.id
                                ? "bg-primary text-primary-foreground"
                                : steps.findIndex((st) => st.id === step) > i
                                    ? "bg-success text-success-foreground"
                                    : "bg-secondary text-muted-foreground"
                                }`}
                        >
                            {steps.findIndex((st) => st.id === step) > i ? (
                                <Check className="h-4 w-4" />
                            ) : (
                                i + 1
                            )}
                        </div>
                        {i < steps.length - 1 && (
                            <div
                                className={`w-12 h-0.5 mx-2 transition-all ${steps.findIndex((st) => st.id === step) > i
                                    ? "bg-success"
                                    : "bg-border"
                                    }`}
                            />
                        )}
                    </div>
                ))}
            </div>

            {/* Step Content */}
            {step === "welcome" && (
                <Card className="border-border/50">
                    <CardHeader className="text-center">
                        <div className="mx-auto h-16 w-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-4">
                            <Sparkles className="h-8 w-8 text-primary" />
                        </div>
                        <CardTitle className="text-2xl">Bem-vindo ao Meeting Assistant!</CardTitle>
                        <CardDescription className="text-base">
                            Vamos configurar sua conta em alguns passos simples.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="fullName">Como podemos te chamar?</Label>
                            <Input
                                id="fullName"
                                placeholder="Seu nome"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="h-12 text-base"
                                disabled={loading}
                            />
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                                {error}
                            </div>
                        )}

                        <Button
                            onClick={handleWelcomeNext}
                            className="w-full h-12 text-base"
                            disabled={loading}
                        >
                            {loading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <>
                                    Continuar
                                    <ChevronRight className="h-5 w-5 ml-1" />
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>
            )}

            {step === "connect" && (
                <Card className="border-border/50">
                    <CardHeader className="text-center">
                        <div className="mx-auto h-16 w-16 rounded-2xl bg-info/20 flex items-center justify-center mb-4">
                            <Calendar className="h-8 w-8 text-info" />
                        </div>
                        <CardTitle className="text-2xl">Conecte seu calendário</CardTitle>
                        <CardDescription className="text-base">
                            Permitir acesso ao Google Calendar para detectar suas reuniões automaticamente.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="p-4 rounded-xl bg-secondary/50 border border-border space-y-3">
                            <h4 className="font-medium">O que vamos acessar:</h4>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li className="flex items-center gap-2">
                                    <Check className="h-4 w-4 text-success" />
                                    Ver eventos do seu calendário
                                </li>
                                <li className="flex items-center gap-2">
                                    <Check className="h-4 w-4 text-success" />
                                    Detectar links de reuniões (Meet, Zoom)
                                </li>
                                <li className="flex items-center gap-2">
                                    <Check className="h-4 w-4 text-success" />
                                    Sincronizar automaticamente novos eventos
                                </li>
                            </ul>
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                                {error}
                            </div>
                        )}

                        <div className="space-y-3">
                            <Button
                                onClick={handleConnectGoogle}
                                className="w-full h-12 text-base"
                                disabled={connectingGoogle}
                            >
                                {connectingGoogle ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                    <>
                                        <Calendar className="h-5 w-5 mr-2" />
                                        Conectar Google Calendar
                                    </>
                                )}
                            </Button>

                            <Button
                                variant="ghost"
                                onClick={handleSkip}
                                className="w-full h-10"
                                disabled={connectingGoogle}
                            >
                                Pular por enquanto
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {step === "success" && (
                <Card className="border-border/50">
                    <CardHeader className="text-center">
                        <div className="mx-auto h-16 w-16 rounded-2xl bg-success/20 flex items-center justify-center mb-4">
                            <Check className="h-8 w-8 text-success" />
                        </div>
                        <CardTitle className="text-2xl">Tudo pronto!</CardTitle>
                        <CardDescription className="text-base">
                            Seu calendário foi conectado. O bot entrará automaticamente nas suas reuniões.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="p-4 rounded-xl bg-secondary/50 border border-border space-y-3">
                            <h4 className="font-medium">Como funciona:</h4>
                            <ol className="space-y-3 text-sm text-muted-foreground">
                                <li className="flex gap-3">
                                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-medium">1</span>
                                    <span>Detectamos reuniões com links do Google Meet</span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-medium">2</span>
                                    <span>2 minutos antes, nosso bot entra na reunião</span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-medium">3</span>
                                    <span>Gravamos e transcrevemos automaticamente</span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-medium">4</span>
                                    <span>Acesse tudo no seu dashboard</span>
                                </li>
                            </ol>
                        </div>

                        <Button
                            onClick={handleGoToDashboard}
                            className="w-full h-12 text-base"
                        >
                            Ir para o Dashboard
                            <ArrowRight className="h-5 w-5 ml-2" />
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
