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
            <main className="lg:pl-56">
                <div className="max-w-5xl mx-auto px-6 py-6 pt-16 lg:pt-6">
                    {children}
                </div>
            </main>
        </div>
    );
}
