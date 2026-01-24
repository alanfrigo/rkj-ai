import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * OAuth Callback Route Handler
 * Processes OAuth callbacks and exchanges code for session.
 * PKCE code_verifier is automatically retrieved from cookies by @supabase/ssr.
 */
export async function GET(request: Request) {
    const { searchParams, origin } = new URL(request.url);
    const code = searchParams.get("code");
    const next = searchParams.get("next") ?? "/";

    const redirectOrigin = process.env.NEXT_PUBLIC_APP_URL || origin;

    if (code) {
        const supabase = await createClient();
        const { error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error) {
            const { data: { user } } = await supabase.auth.getUser();

            if (user) {
                const { data: calendars } = await supabase
                    .from("connected_calendars")
                    .select("id")
                    .eq("user_id", user.id)
                    .limit(1);

                if (!calendars || calendars.length === 0) {
                    return NextResponse.redirect(`${redirectOrigin}/onboarding`);
                }
            }

            const redirectPath = next.startsWith("/") ? next : "/";
            return NextResponse.redirect(`${redirectOrigin}${redirectPath}`);
        }

        console.error("[Callback] Error exchanging code:", error.message);
    }

    return NextResponse.redirect(`${redirectOrigin}/login?error=auth_error`);
}
