"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Chrome, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Logo } from "@/components/ui/logo";

export default function SignupClient() {
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const router = useRouter();
    const supabase = createClient();

    const handleEmailSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        // Use NEXT_PUBLIC_APP_URL to ensure consistent URL for redirects
        const appUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;

        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName,
                },
                emailRedirectTo: `${appUrl}/callback`,
            },
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        setSuccess(true);
        setLoading(false);
    };

    const handleGoogleSignup = async () => {
        setGoogleLoading(true);
        setError(null);

        // Use NEXT_PUBLIC_APP_URL to ensure consistent URL for PKCE flow
        const appUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;

        const { error } = await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${appUrl}/callback`,
                scopes: "email profile",
            },
        });

        if (error) {
            setError(error.message);
            setGoogleLoading(false);
        }
    };

    if (success) {
        return (
            <div className="animate-fade-in space-y-6">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                    <CardHeader className="space-y-1 text-center">
                        <div className="mx-auto h-16 w-16 rounded-full bg-success/20 flex items-center justify-center mb-4">
                            <Mail className="h-8 w-8 text-success" />
                        </div>
                        <CardTitle className="text-2xl font-bold">Verifique seu email</CardTitle>
                        <CardDescription className="text-base">
                            Enviamos um link de confirmação para <strong>{email}</strong>
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="text-center">
                        <p className="text-sm text-muted-foreground">
                            Clique no link no seu email para ativar sua conta e começar a usar o Meeting Assistant.
                        </p>
                    </CardContent>
                    <CardFooter className="justify-center">
                        <Link href="/login">
                            <Button variant="outline">Voltar para login</Button>
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    return (
        <div className="animate-fade-in space-y-6">
            {/* Mobile logo */}
            <div className="lg:hidden flex justify-center mb-8">
                <Logo size="lg" />
            </div>

            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold">Criar conta</CardTitle>
                    <CardDescription>
                        Comece a gravar suas reuniões automaticamente
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                    {/* Google Signup */}
                    <Button
                        variant="outline"
                        className="w-full h-12 text-base"
                        onClick={handleGoogleSignup}
                        disabled={googleLoading || loading}
                    >
                        {googleLoading ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <>
                                <Chrome className="h-5 w-5 mr-2" />
                                Continuar com Google
                            </>
                        )}
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-border" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-card px-2 text-muted-foreground">
                                ou cadastre com email
                            </span>
                        </div>
                    </div>

                    {/* Email Signup Form */}
                    <form onSubmit={handleEmailSignup} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="fullName">Nome completo</Label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="fullName"
                                    type="text"
                                    placeholder="Seu nome"
                                    className="pl-10"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    required
                                    disabled={loading || googleLoading}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="seu@email.com"
                                    className="pl-10"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={loading || googleLoading}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Senha</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="password"
                                    type="password"
                                    placeholder="Mínimo 6 caracteres"
                                    className="pl-10"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    minLength={6}
                                    disabled={loading || googleLoading}
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                                {error}
                            </div>
                        )}

                        <Button
                            type="submit"
                            className="w-full h-12 text-base"
                            disabled={loading || googleLoading}
                        >
                            {loading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                "Criar conta"
                            )}
                        </Button>

                        <p className="text-xs text-muted-foreground text-center">
                            Ao criar uma conta, você concorda com nossos{" "}
                            <Link href="/terms-and-conditions" className="text-primary hover:underline">
                                Termos de Uso
                            </Link>{" "}
                            e{" "}
                            <Link href="/privacy-policy" className="text-primary hover:underline">
                                Política de Privacidade
                            </Link>
                        </p>
                    </form>
                </CardContent>

                <CardFooter className="flex flex-col space-y-4 pt-0">
                    <p className="text-sm text-muted-foreground text-center">
                        Já tem uma conta?{" "}
                        <Link href="/login" className="text-primary hover:underline font-medium">
                            Entrar
                        </Link>
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
