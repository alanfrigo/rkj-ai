import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Updates user session and handles auth redirects.
 * Called by proxy.ts for protected routes.
 * 
 * Also adds security headers to all responses.
 * 
 * Onboarding is handled specially:
 * - Unauthenticated users are redirected to login
 * - Authenticated users WITH calendar are redirected to dashboard
 * - Authenticated users WITHOUT calendar can access onboarding
 */
export async function updateSession(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Public routes - skip auth check entirely
    const publicRoutes = ["/", "/login", "/signup", "/callback", "/auth/callback", "/api/auth"];
    const isPublicRoute = publicRoutes.some((route) =>
        pathname.startsWith(route) || pathname === route
    );

    // Helper to add security headers to response
    const addSecurityHeaders = (response: NextResponse): NextResponse => {
        response.headers.set("X-Content-Type-Options", "nosniff");
        response.headers.set("X-Frame-Options", "DENY");
        response.headers.set("X-XSS-Protection", "1; mode=block");
        response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
        response.headers.set(
            "Content-Security-Policy",
            "frame-ancestors 'none'; form-action 'self';"
        );
        return response;
    };

    if (isPublicRoute) {
        return addSecurityHeaders(NextResponse.next({ request }));
    }

    // Skip auth check for static assets
    if (
        pathname.startsWith("/_next") ||
        pathname.startsWith("/static") ||
        pathname.includes(".")
    ) {
        return addSecurityHeaders(NextResponse.next({ request }));
    }

    let supabaseResponse = NextResponse.next({ request });

    // MUST use the same URL as browser for PKCE cookie key consistency
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;

    const supabase = createServerClient(
        supabaseUrl,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) =>
                        request.cookies.set(name, value)
                    );
                    supabaseResponse = NextResponse.next({ request });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options)
                    );
                },
            },
        }
    );

    const { data: { user } } = await supabase.auth.getUser();

    // Handle onboarding route specifically
    const isOnboardingRoute = pathname.startsWith("/onboarding");

    if (!user) {
        // API routes return 401 for unauthenticated requests
        if (pathname.startsWith("/api/")) {
            return Response.json(
                { error: "Unauthorized", message: "Authentication required" },
                { status: 401 }
            );
        }

        // Unauthenticated users trying to access onboarding go to login
        if (isOnboardingRoute) {
            const url = request.nextUrl.clone();
            url.pathname = "/login";
            return NextResponse.redirect(url);
        }

        // Browser routes redirect to login
        const url = request.nextUrl.clone();
        url.pathname = "/login";
        url.searchParams.set("redirect", pathname);
        return NextResponse.redirect(url);
    }

    // User is authenticated - check onboarding completion for /onboarding route
    if (isOnboardingRoute) {
        // Check if user has already completed onboarding (has connected calendar)
        const { data: calendars } = await supabase
            .from("connected_calendars")
            .select("id")
            .eq("user_id", user.id)
            .eq("is_active", true)
            .limit(1);

        const hasCompletedOnboarding = calendars && calendars.length > 0;

        if (hasCompletedOnboarding) {
            // User already has a calendar connected, redirect to dashboard
            const url = request.nextUrl.clone();
            url.pathname = "/dashboard";
            return NextResponse.redirect(url);
        }

        // User needs onboarding, allow access
        return addSecurityHeaders(supabaseResponse);
    }

    return addSecurityHeaders(supabaseResponse);
}

