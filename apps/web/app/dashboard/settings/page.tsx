export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import {
    User,
    Calendar,
    Bell,
    Shield,
    Trash2,
    ExternalLink
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { LabeledSwitch } from "@/components/ui/switch";
import { UserAvatar } from "@/components/ui/avatar";

export default async function SettingsPage() {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    const { data: profile } = await supabase
        .from("users")
        .select("*")
        .eq("id", user?.id)
        .single();

    const { data: calendars } = await supabase
        .from("connected_calendars")
        .select("*")
        .eq("user_id", user?.id);

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Configurações</h1>
                <p className="text-muted-foreground mt-1">
                    Gerencie sua conta e preferências
                </p>
            </div>

            <div className="grid gap-6">
                {/* Profile */}
                <Card className="border-border/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <User className="h-5 w-5" />
                            Perfil
                        </CardTitle>
                        <CardDescription>
                            Suas informações pessoais
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center gap-4">
                            <UserAvatar
                                name={profile?.full_name || user?.email || "User"}
                                size="lg"
                            />
                            <div>
                                <p className="font-medium">{profile?.full_name || "Usuário"}</p>
                                <p className="text-sm text-muted-foreground">{user?.email}</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Nome</Label>
                                <Input id="name" defaultValue={profile?.full_name || ""} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input id="email" value={user?.email || ""} disabled />
                            </div>
                        </div>
                        <Button>Salvar alterações</Button>
                    </CardContent>
                </Card>

                {/* Connected Calendars */}
                <Card className="border-border/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="h-5 w-5" />
                            Calendários Conectados
                        </CardTitle>
                        <CardDescription>
                            Gerencie os calendários sincronizados
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {calendars && calendars.length > 0 ? (
                            <div className="space-y-3">
                                {calendars.map((calendar) => (
                                    <div
                                        key={calendar.id}
                                        className="flex items-center justify-between p-4 rounded-xl bg-secondary/30"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-lg bg-success/20 flex items-center justify-center">
                                                <Calendar className="h-5 w-5 text-success" />
                                            </div>
                                            <div>
                                                <p className="font-medium">{calendar.calendar_name || "Google Calendar"}</p>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-sm text-muted-foreground capitalize">
                                                        {calendar.provider}
                                                    </span>
                                                    <Badge variant={calendar.is_active ? "success" : "secondary"}>
                                                        {calendar.is_active ? "Ativo" : "Inativo"}
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <div className="h-12 w-12 rounded-xl bg-muted mx-auto flex items-center justify-center mb-4">
                                    <Calendar className="h-6 w-6 text-muted-foreground" />
                                </div>
                                <p className="text-muted-foreground mb-4">
                                    Nenhum calendário conectado
                                </p>
                                <Button>
                                    Conectar Google Calendar
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Notifications */}
                <Card className="border-border/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bell className="h-5 w-5" />
                            Notificações
                        </CardTitle>
                        <CardDescription>
                            Configure como você recebe notificações
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            <LabeledSwitch
                                label="Notificações por email"
                                description="Receba emails quando reuniões forem gravadas"
                                defaultChecked={profile?.settings?.email_notifications ?? true}
                            />
                            <LabeledSwitch
                                label="Gravação automática"
                                description="Gravar automaticamente todas as reuniões"
                                defaultChecked={profile?.settings?.auto_record ?? true}
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Danger Zone */}
                <Card className="border-destructive/30">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-destructive">
                            <Shield className="h-5 w-5" />
                            Zona de Perigo
                        </CardTitle>
                        <CardDescription>
                            Ações irreversíveis
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-medium">Excluir conta</p>
                                <p className="text-sm text-muted-foreground">
                                    Remover permanentemente sua conta e todos os dados
                                </p>
                            </div>
                            <Button variant="destructive" size="sm">
                                Excluir conta
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
