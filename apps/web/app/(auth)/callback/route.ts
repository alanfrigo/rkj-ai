import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get("code");
    const origin = requestUrl.origin;

    if (code) {
        const supabase = await createClient();
        const { error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error) {
            // Check if user needs onboarding (no connected calendars)
            const { data: { user } } = await supabase.auth.getUser();

            if (user) {
                const { data: calendars } = await supabase
                    .from("connected_calendars")
                    .select("id")
                    .eq("user_id", user.id)
                    .limit(1);

                // If no calendars connected, redirect to onboarding
                if (!calendars || calendars.length === 0) {
                    return NextResponse.redirect(`${origin}/onboarding`);
                }
            }

            return NextResponse.redirect(origin);
        }
    }

    // If there's an error, redirect to login with error
    return NextResponse.redirect(`${origin}/login?error=auth_error`);
}
