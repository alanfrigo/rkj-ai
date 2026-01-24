// Force dynamic rendering - this is a server component wrapper
export const dynamic = "force-dynamic";

import OnboardingClient from "./client";

export default function OnboardingPage() {
    return <OnboardingClient />;
}
