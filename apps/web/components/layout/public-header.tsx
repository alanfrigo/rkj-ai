import Link from "next/link";
import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { createClient } from "@/lib/supabase/server";

interface PublicHeaderProps {
  variant?: "full" | "simple";
  maxWidth?: "sm" | "md" | "lg" | "xl" | "6xl" | "4xl";
}

export async function PublicHeader({
  variant = "full",
  maxWidth = "6xl",
}: PublicHeaderProps) {
  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "4xl": "max-w-4xl",
    "6xl": "max-w-6xl",
  };

  if (variant === "simple") {
    return (
      <header className="border-b border-border bg-card">
        <div className={`mx-auto ${maxWidthClasses[maxWidth]} px-6 py-4`}>
          <Link href="/">
            <Logo size="md" />
          </Link>
        </div>
      </header>
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-sm">
      <div
        className={`mx-auto ${maxWidthClasses[maxWidth]} px-6 h-14 flex items-center justify-between`}
      >
        <Link href="/">
          <Logo size="sm" />
        </Link>

        <nav className="flex items-center gap-4">
          <ThemeToggle />
          {user ? (
            <Button asChild size="sm">
              <Link href="/dashboard">Acessar App</Link>
            </Button>
          ) : (
            <Button asChild size="sm">
              <Link href="/login">Entrar</Link>
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
}
