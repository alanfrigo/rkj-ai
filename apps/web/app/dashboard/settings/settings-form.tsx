"use client";

import { useState, useTransition } from "react";
import { LabeledSwitch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw, Bot, Check } from "lucide-react";

interface SettingsFormProps {
    initialSettings: {
        auto_sync_calendar?: boolean;
        auto_record?: boolean;
        email_notifications?: boolean;
        notifications_enabled?: boolean;
        bot_display_name?: string;
        bot_camera_enabled?: boolean;
    };
}


async function updatePreference(key: string, value: boolean | string) {
    const response = await fetch("/api/settings/preferences", {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ [key]: value }),
    });

    if (!response.ok) {
        throw new Error("Failed to update preference");
    }

    return response.json();
}


export function SettingsForm({ initialSettings }: SettingsFormProps) {
    const [settings, setSettings] = useState(initialSettings);
    const [isPending, startTransition] = useTransition();
    const [syncTriggered, setSyncTriggered] = useState(false);
    const [botNameSaving, setBotNameSaving] = useState(false);
    const [botNameSaved, setBotNameSaved] = useState(false);

    const handleToggle = (key: keyof typeof settings, value: boolean) => {
        startTransition(async () => {
            try {
                const result = await updatePreference(key, value);
                setSettings((prev) => ({ ...prev, [key]: value }));

                if (key === "auto_sync_calendar" && result.sync_triggered) {
                    setSyncTriggered(true);
                    setTimeout(() => setSyncTriggered(false), 3000);
                }
            } catch (error) {
                console.error("Failed to update setting:", error);
                // Revert on error
                setSettings((prev) => ({ ...prev, [key]: !value }));
            }
        });
    };

    const handleBotNameChange = (value: string) => {
        setSettings((prev) => ({ ...prev, bot_display_name: value }));
        setBotNameSaved(false);
    };

    const handleSaveBotName = async () => {
        setBotNameSaving(true);
        try {
            await updatePreference("bot_display_name", settings.bot_display_name ?? "");
            setBotNameSaved(true);
            setTimeout(() => setBotNameSaved(false), 3000);
        } catch (error) {
            console.error("Failed to save bot name:", error);
        } finally {
            setBotNameSaving(false);
        }
    };

    return (
        <div className="rounded-lg border border-border bg-card divide-y divide-border">
            {/* Auto Sync Calendar */}
            <div className="p-4">
                <div className="flex items-center justify-between">
                    <div className="flex-1">
                        <LabeledSwitch
                            label="Sincronização automática de calendário"
                            description="Sincronizar eventos automaticamente pelos próximos 7 dias"
                            checked={settings.auto_sync_calendar ?? true}
                            onCheckedChange={(checked) =>
                                handleToggle("auto_sync_calendar", checked)
                            }
                            disabled={isPending}
                        />
                    </div>
                    {syncTriggered && (
                        <div className="flex items-center gap-2 text-xs text-success ml-4">
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            <span>Sincronizando...</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Email Notifications */}
            <div className="p-4">
                <LabeledSwitch
                    label="Notificações por email"
                    description="Receba emails quando reuniões forem gravadas"
                    checked={settings.email_notifications ?? true}
                    onCheckedChange={(checked) =>
                        handleToggle("email_notifications", checked)
                    }
                    disabled={isPending}
                />
            </div>

            {/* Auto Record */}
            <div className="p-4">
                <LabeledSwitch
                    label="Gravação automática"
                    description="Gravar automaticamente todas as reuniões detectadas"
                    checked={settings.auto_record ?? true}
                    onCheckedChange={(checked) =>
                        handleToggle("auto_record", checked)
                    }
                    disabled={isPending}
                />
            </div>

            {/* Bot Display Name */}
            <div className="p-4">
                <div className="flex items-start gap-3">
                    <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 space-y-2">
                        <div>
                            <label htmlFor="bot-name" className="text-sm font-medium">
                                Nome do Bot
                            </label>
                            <p className="text-xs text-muted-foreground">
                                Nome exibido quando o bot entrar nas reuniões
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Input
                                id="bot-name"
                                value={settings.bot_display_name ?? "RKJ.AI"}
                                onChange={(e) => handleBotNameChange(e.target.value)}
                                placeholder="RKJ.AI"
                                className="max-w-xs"
                            />
                            <Button
                                size="sm"
                                onClick={handleSaveBotName}
                                disabled={botNameSaving}
                            >
                                {botNameSaving ? (
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                ) : botNameSaved ? (
                                    <><Check className="h-4 w-4 mr-1" /> Salvo</>
                                ) : (
                                    "Salvar"
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bot Camera */}
            <div className="p-4">
                <LabeledSwitch
                    label="Câmera do Bot habilitada"
                    description="Quando desabilitada, o bot entra nas reuniões sem vídeo"
                    checked={settings.bot_camera_enabled ?? false}
                    onCheckedChange={(checked) =>
                        handleToggle("bot_camera_enabled", checked)
                    }
                    disabled={isPending}
                />
            </div>
        </div>
    );
}
