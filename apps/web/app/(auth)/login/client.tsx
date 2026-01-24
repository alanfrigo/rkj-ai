"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Video, Mail, Lock, Chrome, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginClient() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const supabase = createClient();

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        router.push("/");
        router.refresh();
    };

    const handleGoogleLogin = async () => {
        setGoogleLoading(true);
        setError(null);

        // Use NEXT_PUBLIC_APP_URL to ensure consistent URL for PKCE flow
        // This prevents code_verifier mismatch when accessing via 0.0.0.0 vs localhost
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

    return (
        <div className="animate-fade-in space-y-6">
            {/* Mobile logo */}
            <div className="lg:hidden flex justify-center mb-8">
                <div className="flex items-center gap-2">
                    <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
                        <Video className="h-5 w-5 text-primary-foreground" />
                    </div>
                    <span className="text-xl font-bold">Meeting Assistant</span>
                </div>
            </div>

            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold">Bem-vindo de volta</CardTitle>
                    <CardDescription>
                        Entre na sua conta para continuar
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                    {/* Google Login */}
                    <Button
                        variant="outline"
                        className="w-full h-12 text-base"
                        onClick={handleGoogleLogin}
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
                                ou continue com email
                            </span>
                        </div>
                    </div>

                    {/* Email Login Form */}
                    <form onSubmit={handleEmailLogin} className="space-y-4">
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
                                    placeholder="••••••••"
                                    className="pl-10"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
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
                                "Entrar"
                            )}
                        </Button>
                    </form>
                </CardContent>

                <CardFooter className="flex flex-col space-y-4 pt-0">
                    <p className="text-sm text-muted-foreground text-center">
                        Não tem uma conta?{" "}
                        <Link href="/signup" className="text-primary hover:underline font-medium">
                            Criar conta
                        </Link>
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
