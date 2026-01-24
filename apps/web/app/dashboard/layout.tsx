import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-background">
            <Sidebar />
            {/* Main content area with sidebar offset */}
            <main className="lg:pl-64">
                <div className="container max-w-6xl mx-auto px-4 py-8 pt-20 lg:pt-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
