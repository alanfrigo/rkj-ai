import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get("code");
    const origin = requestUrl.origin;

    if (code) {
        const supabase = await createClient();
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error && data.session) {
            const { user, session } = data;

            // Store the refresh token for calendar access
            // The Google OAuth flow returns tokens we need to save
            if (session.provider_refresh_token) {
                await supabase
                    .from("users")
                    .update({
                        google_refresh_token: session.provider_refresh_token,
                        google_token_expires_at: new Date(Date.now() + (session.expires_in || 3600) * 1000).toISOString(),
                    })
                    .eq("id", user.id);

                // Create a connected calendar entry
                // For now we'll use a placeholder - the scheduler will sync actual calendars
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
            }

            // Redirect to success page
            return NextResponse.redirect(`${origin}/onboarding?step=success`);
        }
    }

    // If there's an error, redirect back to onboarding
    return NextResponse.redirect(`${origin}/onboarding?error=calendar_error`);
}
