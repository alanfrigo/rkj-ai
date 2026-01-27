import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { v4 as uuidv4 } from "uuid";

export async function POST(request: Request) {
    try {
        const supabase = await createClient();

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json(
                { error: "Unauthorized" },
                { status: 401 }
            );
        }

        const body = await request.json();
        const { meetingUrl, title } = body;

        // Validate meeting URL
        if (!meetingUrl) {
            return NextResponse.json(
                { error: "Meeting URL is required" },
                { status: 400 }
            );
        }

        // Check if it's a valid Google Meet URL
        const meetPattern = /^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}$/i;
        if (!meetPattern.test(meetingUrl)) {
            return NextResponse.json(
                { error: "Invalid Google Meet URL format" },
                { status: 400 }
            );
        }

        const meetingId = uuidv4();
        const meetingTitle = title || `Reunião Manual - ${new Date().toLocaleString("pt-BR")}`;

        // Create meeting record
        const { data: meeting, error: meetingError } = await supabase
            .from("meetings")
            .insert({
                id: meetingId,
                user_id: user.id,
                title: meetingTitle,
                meeting_url: meetingUrl,
                meeting_provider: "google_meet",
                status: "joining",
                scheduled_start: new Date().toISOString(),
            })
            .select()
            .single();

        if (meetingError) {
            console.error("Error creating meeting:", meetingError);
            return NextResponse.json(
                { error: "Failed to create meeting" },
                { status: 500 }
            );
        }

        // Queue bot job via Redis
        try {
            // Fetch user settings for bot configuration
            const { data: profile } = await supabase
                .from("users")
                .select("settings")
                .eq("id", user.id)
                .single();

            const botDisplayName = profile?.settings?.bot_display_name ?? "Meeting Assistant Bot 🤖";
            const botCameraEnabled = profile?.settings?.bot_camera_enabled ?? false;

            const Redis = require("ioredis");
            const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

            const jobData = {
                id: uuidv4(),
                type: "join_meeting",
                data: {
                    meeting_id: meetingId,
                    meeting_url: meetingUrl,
                    user_id: user.id,
                    bot_display_name: botDisplayName,
                    bot_camera_enabled: botCameraEnabled,
                },
                created_at: new Date().toISOString()
            };

            // Push to the same queue the orchestrator is listening to
            // default queue name: "queue:join_meeting"
            await redis.rpush("queue:join_meeting", JSON.stringify(jobData));

            // Close connection to prevent leaks in serverless/lambda environment
            redis.quit();

        } catch (queueError) {
            console.error("Failed to queue job:", queueError);
            // Don't fail the request - the bot might not start immediately but the record is created
        }

        return NextResponse.json({
            success: true,
            meeting: {
                id: meeting.id,
                title: meeting.title,
                status: meeting.status,
            },
        });
    } catch (error) {
        console.error("Error in join-meeting API:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
