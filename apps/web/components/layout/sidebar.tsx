"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    Mic,
    LayoutDashboard,
    Video,
    Settings,
    LogOut,
    Menu,
    X,
} from "lucide-react";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";

interface NavItem {
    label: string;
    href: string;
    icon: React.ReactNode;
}

const navItems: NavItem[] = [
    { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Reuniões", href: "/dashboard/meetings", icon: <Video className="h-4 w-4" /> },
    { label: "Configurações", href: "/dashboard/settings", icon: <Settings className="h-4 w-4" /> },
];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [mobileOpen, setMobileOpen] = useState(false);
    const supabase = createClient();

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push("/login");
    };

    const NavContent = () => (
        <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="h-14 flex items-center px-4">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded-md bg-primary/10 flex items-center justify-center">
                        <Mic className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <span className="font-display text-base font-semibold tracking-tight">
                        RKJ.AI
                    </span>
                </Link>
            </div>

            {/* Nav Items */}
            <nav className="flex-1 px-2 py-2">
                <div className="space-y-0.5">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href ||
                            (item.href !== "/dashboard" && pathname.startsWith(item.href));

                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                onClick={() => setMobileOpen(false)}
                                className={cn(
                                    "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors",
                                    isActive
                                        ? "bg-primary/10 text-primary font-medium"
                                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                                )}
                            >
                                {item.icon}
                                {item.label}
                            </Link>
                        );
                    })}
                </div>
            </nav>

            {/* Footer */}
            <div className="p-2 border-t border-border">
                <div className="flex items-center justify-between px-3 py-2 text-xs text-muted-foreground">
                    <span>Tema</span>
                    <ThemeToggle />
                </div>
                <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors"
                >
                    <LogOut className="h-4 w-4" />
                    Sair
                </button>
            </div>
        </div>
    );

    return (
        <>
            {/* Mobile Toggle */}
            <button
                className="lg:hidden fixed top-3 left-3 z-50 h-9 w-9 rounded-md bg-card border border-border flex items-center justify-center"
                onClick={() => setMobileOpen(!mobileOpen)}
            >
                {mobileOpen ? (
                    <X className="h-4 w-4" />
                ) : (
                    <Menu className="h-4 w-4" />
                )}
            </button>

            {/* Mobile Overlay */}
            {mobileOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Mobile Sidebar */}
            <aside
                className={cn(
                    "lg:hidden fixed inset-y-0 left-0 z-40 w-56 bg-card border-r border-border transform transition-transform duration-200",
                    mobileOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <NavContent />
            </aside>

            {/* Desktop Sidebar */}
            <aside className="hidden lg:block fixed inset-y-0 left-0 w-56 bg-card border-r border-border">
                <NavContent />
            </aside>
        </>
    );
}
