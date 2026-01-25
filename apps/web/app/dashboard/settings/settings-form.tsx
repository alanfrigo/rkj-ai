"use client";

import { useState, useTransition } from "react";
import { LabeledSwitch } from "@/components/ui/switch";
import { RefreshCw } from "lucide-react";

interface SettingsFormProps {
    initialSettings: {
        auto_sync_calendar?: boolean;
        auto_record?: boolean;
        email_notifications?: boolean;
        notifications_enabled?: boolean;
    };
}

async function updatePreference(key: string, value: boolean) {
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
        </div>
    );
}
