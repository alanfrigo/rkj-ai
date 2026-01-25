import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function GET() {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { data: profile } = await supabase
        .from("users")
        .select("settings")
        .eq("id", user.id)
        .single();

    const defaults = {
        auto_record: true,
        default_language: "pt-BR",
        notifications_enabled: true,
        email_notifications: true,
        auto_sync_calendar: true,
    };

    const settings = { ...defaults, ...(profile?.settings || {}) };

    return NextResponse.json({ settings });
}

export async function PATCH(request: NextRequest) {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const updates = await request.json();

    // Get current settings
    const { data: profile } = await supabase
        .from("users")
        .select("settings")
        .eq("id", user.id)
        .single();

    const currentSettings = profile?.settings || {};
    const wasSyncDisabled = currentSettings.auto_sync_calendar === false;

    // Merge updates with current settings
    const newSettings = { ...currentSettings, ...updates };

    // Update database
    const { error } = await supabase
        .from("users")
        .update({ settings: newSettings })
        .eq("id", user.id);

    if (error) {
        console.error("Failed to update settings:", error);
        return NextResponse.json(
            { error: "Failed to update settings" },
            { status: 500 }
        );
    }

    // Check if sync was re-enabled
    let syncTriggered = false;
    if (wasSyncDisabled && updates.auto_sync_calendar === true) {
        // In a real implementation, this would call the scheduler service
        // For now, we just flag that sync should be triggered
        syncTriggered = true;
        console.log(`Sync re-enabled for user ${user.id}, triggering immediate sync`);
    }

    return NextResponse.json({
        settings: newSettings,
        sync_triggered: syncTriggered,
    });
}
