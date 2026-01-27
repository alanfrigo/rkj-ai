import { PublicHeader } from "@/components/layout/public-header";
import { PublicFooter } from "@/components/layout/public-footer";

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PublicHeader variant="full" maxWidth="6xl" />
      <main className="flex-1">{children}</main>
      <PublicFooter variant="full" maxWidth="6xl" />
    </div>
  );
}
