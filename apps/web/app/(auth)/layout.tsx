import { Mic, CheckCircle2 } from "lucide-react";

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen flex">
            {/* Left side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-card border-r border-border items-center justify-center p-12">
                <div className="max-w-md space-y-10">
                    <div className="flex items-center gap-3">
                        <div className="h-11 w-11 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Mic className="h-5 w-5 text-primary" />
                        </div>
                        <span className="font-display text-2xl font-semibold tracking-tight">RKJ.AI</span>
                    </div>

                    <div className="space-y-4">
                        <h1 className="text-3xl font-display leading-tight text-balance">
                            Suas reuniões, documentadas automaticamente
                        </h1>
                        <p className="text-muted-foreground">
                            Grave, transcreva e pesquise todas as suas reuniões do Google Meet e Zoom.
                        </p>
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                            <span>Gravação automática de reuniões</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                            <span>Transcrição com IA em português</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                            <span>Busca por palavra-chave</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
                            <span>Sincronização com Google Calendar</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right side - Auth content */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-background">
                <div className="w-full max-w-sm">
                    {children}
                </div>
            </div>
        </div>
    );
}
