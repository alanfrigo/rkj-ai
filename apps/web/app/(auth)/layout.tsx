import { Video } from "lucide-react";

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen flex">
            {/* Left side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary/20 via-background to-background items-center justify-center p-12">
                <div className="max-w-md space-y-8">
                    <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center">
                            <Video className="h-6 w-6 text-primary-foreground" />
                        </div>
                        <span className="text-2xl font-bold">Meeting Assistant</span>
                    </div>

                    <div className="space-y-4">
                        <h1 className="text-4xl font-bold leading-tight">
                            Nunca mais perca o que aconteceu nas suas reuniões
                        </h1>
                        <p className="text-lg text-muted-foreground">
                            Grave, transcreva e pesquise automaticamente todas as suas reuniões
                            do Google Meet e Zoom.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4">
                        <div className="p-4 rounded-xl bg-card/50 border border-border">
                            <div className="text-2xl font-bold text-primary">100%</div>
                            <div className="text-sm text-muted-foreground">Automático</div>
                        </div>
                        <div className="p-4 rounded-xl bg-card/50 border border-border">
                            <div className="text-2xl font-bold text-primary">IA</div>
                            <div className="text-sm text-muted-foreground">Transcrição</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right side - Auth content */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
                <div className="w-full max-w-md">
                    {children}
                </div>
            </div>
        </div>
    );
}
