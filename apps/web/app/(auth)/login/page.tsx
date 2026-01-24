// Force dynamic rendering - this is a server component wrapper
export const dynamic = "force-dynamic";

import LoginClient from "./client";

export default function LoginPage() {
    return <LoginClient />;
}
