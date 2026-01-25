import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ eventId: string }> }
) {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { eventId } = await params;

    // Verify ownership
    const { data: event, error: fetchError } = await supabase
        .from("calendar_events")
        .select("id, user_id, title")
        .eq("id", eventId)
        .single();

    if (fetchError || !event) {
        return NextResponse.json({ error: "Event not found" }, { status: 404 });
    }

    if (event.user_id !== user.id) {
        return NextResponse.json({ error: "Access denied" }, { status: 403 });
    }

    // Mark as excluded
    const { error: updateError } = await supabase
        .from("calendar_events")
        .update({ is_excluded: true })
        .eq("id", eventId);

    if (updateError) {
        console.error("Failed to exclude event:", updateError);
        return NextResponse.json(
            { error: "Failed to exclude event" },
            { status: 500 }
        );
    }

    console.log(`Event ${eventId} "${event.title}" excluded by user ${user.id}`);

    return NextResponse.json({
        message: "Event excluded",
        eventId,
        excluded: true,
    });
}
