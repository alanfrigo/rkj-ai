import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function RootPage() {
  const supabase = await createClient();

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    // Not logged in - redirect to login
    redirect("/login");
  }

  // Check if user has connected calendars (onboarding completed)
  const { data: calendars } = await supabase
    .from("connected_calendars")
    .select("id")
    .eq("user_id", user.id)
    .limit(1);

  if (!calendars || calendars.length === 0) {
    // No calendars - redirect to onboarding
    redirect("/onboarding");
  }

  // Has calendars - redirect to dashboard
  redirect("/dashboard");
}
