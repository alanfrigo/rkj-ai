import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * POST /api/calendar/sync
 * Triggers an immediate calendar sync for the current user.
 * Calls the backend API to sync calendar events.
 */
export async function POST() {
    try {
        const supabase = await createClient();
        const { data: { user } } = await supabase.auth.getUser();

        if (!user) {
            return NextResponse.json(
                { error: "Unauthorized" },
                { status: 401 }
            );
        }

        // Get the access token for the API call
        const { data: { session } } = await supabase.auth.getSession();
        const accessToken = session?.access_token;

        if (!accessToken) {
            return NextResponse.json(
                { error: "No access token available" },
                { status: 401 }
            );
        }

        // Call the backend API to sync calendar
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        const response = await fetch(`${apiUrl}/api/calendar/sync`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("[Calendar Sync] Backend API error:", errorData);
            return NextResponse.json(
                { error: "Failed to sync calendar", details: errorData },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json({
            message: "Calendar sync triggered",
            ...data,
        });
    } catch (error) {
        console.error("[Calendar Sync] Error:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
