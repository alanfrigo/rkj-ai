"use client";

import { useState, useTransition } from "react";
import { X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface ExcludeEventButtonProps {
    eventId: string;
    title: string;
}

export function ExcludeEventButton({ eventId, title }: ExcludeEventButtonProps) {
    const [isPending, startTransition] = useTransition();
    const router = useRouter();

    const handleExclude = () => {
        if (!confirm(`Excluir "${title}" do sistema?\n\nIsso não removerá o evento do seu calendário real.`)) {
            return;
        }

        startTransition(async () => {
            try {
                const response = await fetch(`/api/calendar/events/${eventId}/exclude`, {
                    method: "PATCH",
                });

                if (!response.ok) {
                    throw new Error("Failed to exclude event");
                }

                // Refresh the page to update the list
                router.refresh();
            } catch (error) {
                console.error("Failed to exclude event:", error);
                alert("Erro ao excluir evento. Tente novamente.");
            }
        });
    };

    return (
        <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleExclude();
            }}
            disabled={isPending}
            title="Excluir do sistema"
        >
            {isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
                <X className="h-3.5 w-3.5" />
            )}
        </Button>
    );
}
