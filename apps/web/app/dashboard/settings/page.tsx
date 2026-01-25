export const dynamic = "force-dynamic";

import { createClient } from "@/lib/supabase/server";
import {
    Calendar,
    Bell,
    Trash2,
    Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
        <div className="animate-fade-in max-w-2xl">
            {/* Header */}
            <header className="mb-8">
                <h1 className="text-2xl font-display">Configurações</h1>
            </header>

            <div className="space-y-8">
                {/* Profile Section */}
                <section>
                    <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-4">
                        Perfil
                    </h2>
                    <div className="rounded-lg border border-border bg-card p-5 space-y-5">
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
                            <div className="space-y-1.5">
                                <label htmlFor="name" className="text-sm text-muted-foreground">
                                    Nome
                                </label>
                                <Input id="name" defaultValue={profile?.full_name || ""} />
                            </div>
                            <div className="space-y-1.5">
                                <label htmlFor="email" className="text-sm text-muted-foreground">
                                    Email
                                </label>
                                <Input id="email" value={user?.email || ""} disabled className="bg-muted/50" />
                            </div>
                        </div>

                        <div className="pt-2">
                            <Button size="sm">Salvar alterações</Button>
                        </div>
                    </div>
                </section>

                {/* Calendars Section */}
                <section>
                    <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-4">
                        Calendários conectados
                    </h2>
                    <div className="rounded-lg border border-border bg-card">
                        {calendars && calendars.length > 0 ? (
                            <div className="divide-y divide-border">
                                {calendars.map((calendar) => (
                                    <div
                                        key={calendar.id}
                                        className="flex items-center justify-between p-4"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="h-9 w-9 rounded-lg bg-success/10 flex items-center justify-center">
                                                <Calendar className="h-4 w-4 text-success" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium">
                                                    {calendar.calendar_name || "Google Calendar"}
                                                </p>
                                                <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                                                    <span className="capitalize">{calendar.provider}</span>
                                                    {calendar.is_active && (
                                                        <>
                                                            <span className="h-1 w-1 rounded-full bg-success" />
                                                            <span className="text-success">Ativo</span>
                                                        </>
                                                    )}
                                                </p>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive hover:bg-destructive/10">
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 text-center">
                                <Calendar className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground mb-4">
                                    Nenhum calendário conectado
                                </p>
                                <Button size="sm">
                                    Conectar Google Calendar
                                </Button>
                            </div>
                        )}
                    </div>
                </section>

                {/* Notifications Section */}
                <section>
                    <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-4">
                        Notificações
                    </h2>
                    <div className="rounded-lg border border-border bg-card divide-y divide-border">
                        <div className="p-4">
                            <LabeledSwitch
                                label="Notificações por email"
                                description="Receba emails quando reuniões forem gravadas"
                                defaultChecked={profile?.settings?.email_notifications ?? true}
                            />
                        </div>
                        <div className="p-4">
                            <LabeledSwitch
                                label="Gravação automática"
                                description="Gravar automaticamente todas as reuniões detectadas"
                                defaultChecked={profile?.settings?.auto_record ?? true}
                            />
                        </div>
                    </div>
                </section>

                {/* Danger Zone */}
                <section>
                    <h2 className="text-xs font-medium text-destructive uppercase tracking-wide mb-4">
                        Zona de perigo
                    </h2>
                    <div className="rounded-lg border border-destructive/30 bg-card p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium">Excluir conta</p>
                                <p className="text-xs text-muted-foreground">
                                    Remover permanentemente sua conta e todos os dados
                                </p>
                            </div>
                            <Button variant="destructive" size="sm">
                                Excluir conta
                            </Button>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
