import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * OAuth Callback Route Handler
 * Processes OAuth callbacks and exchanges code for session.
 * PKCE code_verifier is automatically retrieved from cookies by @supabase/ssr.
 * 
 * Now includes smart detection of Google calendar permissions:
 * - If Google returns a refresh token, calendar access was granted
 * - Automatically creates connected_calendars entry
 * - Triggers immediate calendar sync
 */
export async function GET(request: Request) {
    const { searchParams, origin } = new URL(request.url);
    const code = searchParams.get("code");
    const next = searchParams.get("next") ?? "/";

    const redirectOrigin = process.env.NEXT_PUBLIC_APP_URL || origin;

    if (code) {
        const supabase = await createClient();
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error && data.session) {
            const { user, session } = data;

            // Check if we have an existing calendar connection
            const { data: existingCalendars } = await supabase
                .from("connected_calendars")
                .select("id")
                .eq("user_id", user.id)
                .limit(1);

            const hasCalendar = existingCalendars && existingCalendars.length > 0;

            // If Google returned a refresh token, user granted calendar permissions
            // This can happen on login if they previously granted access
            if (session.provider_refresh_token && !hasCalendar) {
                console.log("[Callback] Google returned refresh token, auto-connecting calendar");

                // Get current user settings to merge with new ones
                const { data: currentUser } = await supabase
                    .from("users")
                    .select("settings")
                    .eq("id", user.id)
                    .single();

                const currentSettings = currentUser?.settings || {};

                // Save the refresh token and enable auto sync
                await supabase
                    .from("users")
                    .update({
                        google_refresh_token: session.provider_refresh_token,
                        google_token_expires_at: new Date(Date.now() + (session.expires_in || 3600) * 1000).toISOString(),
                        settings: {
                            ...currentSettings,
                            auto_sync_calendar: true, // Enable auto sync when calendar is connected
                        },
                    })
                    .eq("id", user.id);

                // Create connected calendar entry
                await supabase.from("connected_calendars").insert({
                    user_id: user.id,
                    provider: "google",
                    calendar_id: "primary",
                    calendar_name: "Google Calendar",
                    is_active: true,
                    is_primary: true,
                });

                // Trigger immediate calendar sync
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                    await fetch(`${apiUrl}/api/calendar/sync`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${session.access_token}`,
                        },
                    });
                    console.log("[Callback] Triggered immediate calendar sync");
                } catch (syncError) {
                    console.error("[Callback] Failed to trigger sync:", syncError);
                    // Non-blocking - scheduler will sync eventually
                }

                // Calendar was auto-connected, go to dashboard
                return NextResponse.redirect(`${redirectOrigin}/dashboard`);
            }

            // No calendar connected and no refresh token - needs onboarding
            if (!hasCalendar) {
                return NextResponse.redirect(`${redirectOrigin}/onboarding`);
            }

            // Already has calendar, go to intended destination
            const redirectPath = next.startsWith("/") ? next : "/";
            return NextResponse.redirect(`${redirectOrigin}${redirectPath}`);
        }

        console.error("[Callback] Error exchanging code:", error?.message);
    }

    return NextResponse.redirect(`${redirectOrigin}/login?error=auth_error`);
}
