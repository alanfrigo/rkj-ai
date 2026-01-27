import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Updates user session and handles auth redirects.
 * Called by proxy.ts for protected routes.
 * 
 * Also adds security headers to all responses.
 */
export async function updateSession(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Public routes - skip auth check
    const publicRoutes = ["/", "/login", "/signup", "/callback", "/auth/callback", "/api/auth", "/onboarding"];
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

    if (!user) {
        // API routes return 401 for unauthenticated requests
        if (pathname.startsWith("/api/")) {
            return Response.json(
                { error: "Unauthorized", message: "Authentication required" },
                { status: 401 }
            );
        }

        // Browser routes redirect to login
        const url = request.nextUrl.clone();
        url.pathname = "/login";
        url.searchParams.set("redirect", pathname);
        return NextResponse.redirect(url);
    }

    return addSecurityHeaders(supabaseResponse);
}
