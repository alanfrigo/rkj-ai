import { PublicHeader } from "@/components/layout/public-header";
import { PublicFooter } from "@/components/layout/public-footer";

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <PublicHeader variant="simple" maxWidth="4xl" />
      <main className="mx-auto max-w-4xl px-6 py-12">{children}</main>
      <PublicFooter variant="compact" maxWidth="4xl" />
    </div>
  );
}
