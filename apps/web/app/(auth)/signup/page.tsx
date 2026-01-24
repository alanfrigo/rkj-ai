// Force dynamic rendering - this is a server component wrapper
export const dynamic = "force-dynamic";

import SignupClient from "./client";

export default function SignupPage() {
    return <SignupClient />;
}
