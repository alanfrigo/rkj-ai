import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

/**
 * Creates a Supabase client for server-side usage.
 * CRITICAL: Uses NEXT_PUBLIC_SUPABASE_URL (same as browser) for cookie key consistency.
 * With Docker extra_hosts mapping, localhost inside the container resolves to the host.
 */
export async function createClient() {
    const cookieStore = await cookies();

    // MUST use the same URL as browser for PKCE cookie key consistency
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;

    return createServerClient(
        supabaseUrl,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return cookieStore.getAll();
                },
                setAll(cookiesToSet) {
                    try {
                        cookiesToSet.forEach(({ name, value, options }) =>
                            cookieStore.set(name, value, options)
                        );
                    } catch {
                        // Server Component context - can be ignored if proxy refreshes sessions
                    }
                },
            },
        }
    );
}
