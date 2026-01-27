import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Calendar OAuth Callback
 * Called when user connects their Google Calendar during onboarding.
 * - Stores refresh token
 * - Creates connected_calendars entry
 * - Triggers immediate calendar sync
 * - Redirects to dashboard (onboarding complete)
 */
export async function GET(request: Request) {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get("code");
    const origin = process.env.NEXT_PUBLIC_APP_URL || requestUrl.origin;

    if (code) {
        const supabase = await createClient();
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error && data.session) {
            const { user, session } = data;

            // Store the refresh token for calendar access
            if (session.provider_refresh_token) {
                // Get current user settings to merge with new ones
                const { data: currentUser } = await supabase
                    .from("users")
                    .select("settings")
                    .eq("id", user.id)
                    .single();

                const currentSettings = currentUser?.settings || {};

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

                // Create a connected calendar entry if it doesn't exist
                const { data: existingCalendar } = await supabase
                    .from("connected_calendars")
                    .select("id")
                    .eq("user_id", user.id)
                    .eq("provider", "google")
                    .limit(1)
                    .single();

                if (!existingCalendar) {
                    await supabase.from("connected_calendars").insert({
                        user_id: user.id,
                        provider: "google",
                        calendar_id: "primary",
                        calendar_name: "Google Calendar",
                        is_active: true,
                        is_primary: true,
                    });
                }

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
                    console.log("[Calendar Callback] Triggered immediate calendar sync");
                } catch (syncError) {
                    console.error("[Calendar Callback] Failed to trigger sync:", syncError);
                    // Non-blocking - scheduler will sync eventually
                }
            }

            // Calendar connected, redirect to dashboard
            // Onboarding is now complete
            return NextResponse.redirect(`${origin}/dashboard`);
        }
    }

    // If there's an error, redirect back to onboarding
    return NextResponse.redirect(`${origin}/onboarding?error=calendar_error`);
}

