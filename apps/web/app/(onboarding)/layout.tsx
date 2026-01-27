"use client";

import { Logo } from "@/components/ui/logo";

export default function OnboardingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border">
                <div className="container max-w-4xl mx-auto px-4 h-16 flex items-center">
                    <Logo size="md" />
                </div>
            </header>

            {/* Content */}
            <main className="container max-w-2xl mx-auto px-4 py-12">
                {children}
            </main>
        </div>
    );
}
