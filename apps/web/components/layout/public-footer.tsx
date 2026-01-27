import Link from "next/link";
import { Logo } from "@/components/ui/logo";

interface PublicFooterProps {
  variant?: "full" | "compact";
  maxWidth?: "sm" | "md" | "lg" | "xl" | "6xl" | "4xl";
}

export function PublicFooter({
  variant = "full",
  maxWidth = "6xl",
}: PublicFooterProps) {
  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "4xl": "max-w-4xl",
    "6xl": "max-w-6xl",
  };

  const currentYear = new Date().getFullYear();

  if (variant === "compact") {
    return (
      <footer className="border-t border-border bg-card">
        <div className={`mx-auto ${maxWidthClasses[maxWidth]} px-6 py-8`}>
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <Logo size="xs" showText={false} />
              <span className="text-sm text-muted-foreground">
                © {currentYear} RKJ.AI. Todos os direitos reservados.
              </span>
            </div>
            <nav className="flex gap-6">
              <Link
                href="/privacy-policy"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Política de Privacidade
              </Link>
              <Link
                href="/terms-and-conditions"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Termos de Serviço
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="border-t border-border bg-card">
      <div className={`mx-auto ${maxWidthClasses[maxWidth]} px-6 py-12`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-4">
            <Logo size="sm" />
            <p className="text-sm text-muted-foreground max-w-xs">
              Grave e transcreva suas reuniões automaticamente. Nunca mais perca
              informações importantes.
            </p>
          </div>

          <div className="space-y-4">
            <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Produto
            </h4>
            <nav className="flex flex-col gap-2">
              <Link
                href="/#features"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Funcionalidades
              </Link>
              <Link
                href="/#how-it-works"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Como funciona
              </Link>
            </nav>
          </div>

          <div className="space-y-4">
            <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Legal
            </h4>
            <nav className="flex flex-col gap-2">
              <Link
                href="/privacy-policy"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Política de Privacidade
              </Link>
              <Link
                href="/terms-and-conditions"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Termos de Serviço
              </Link>
            </nav>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            © {currentYear} RKJ.AI. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </footer>
  );
}
