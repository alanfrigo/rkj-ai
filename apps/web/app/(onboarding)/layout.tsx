"use client";

import { Video, ChevronRight } from "lucide-react";

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
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                            <Video className="h-4 w-4 text-primary-foreground" />
                        </div>
                        <span className="font-bold">Meeting Assistant</span>
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="container max-w-2xl mx-auto px-4 py-12">
                {children}
            </main>
        </div>
    );
}
