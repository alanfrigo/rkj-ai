import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";
import {
  Mic,
  Calendar,
  FileText,
  Search,
  Play,
  CheckCircle2,
  ArrowRight,
  Video,
  Clock,
  Users,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function LandingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />

        <div className="mx-auto max-w-6xl px-6 pt-16 pb-24 md:pt-24 md:pb-32">
          <div className="text-center space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Mic className="h-3.5 w-3.5" />
              <span>Assistente de Reuniões com IA</span>
            </div>

            {/* Headline */}
            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-balance max-w-3xl mx-auto">
              Suas reuniões,{" "}
              <span className="text-primary">documentadas automaticamente</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
              O RKJ.AI entra nas suas reuniões do Google Meet e Zoom, grava e
              transcreve tudo automaticamente. Nunca mais perca informações
              importantes.
            </p>

            {/* CTA */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Button asChild size="lg" className="min-w-[180px]">
                <Link href={user ? "/dashboard" : "/login"}>
                  {user ? "Acessar Dashboard" : "Começar Agora"}
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="min-w-[180px]"
              >
                <Link href="#how-it-works">
                  <Play className="h-4 w-4 mr-2" />
                  Ver como funciona
                </Link>
              </Button>
            </div>

            {/* Trust indicators */}
            <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span>Gravação automática</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span>Transcrição em português</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span>Sync com Google Calendar</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-card border-y border-border">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-semibold tracking-tight mb-4">
              Tudo que você precisa para documentar reuniões
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Automatize o registro das suas reuniões e foque no que realmente
              importa: a conversa.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Sincronização de Calendário
              </h3>
              <p className="text-sm text-muted-foreground">
                Conecte seu Google Calendar e o bot entra automaticamente nas
                suas reuniões agendadas.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Video className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Gravação Automática
              </h3>
              <p className="text-sm text-muted-foreground">
                Grave áudio e vídeo das suas reuniões do Google Meet e Zoom sem
                precisar clicar em nada.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Transcrição com IA
              </h3>
              <p className="text-sm text-muted-foreground">
                Transcrição automática usando OpenAI Whisper com alta precisão
                em português e outros idiomas.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Search className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Busca por Palavra-chave
              </h3>
              <p className="text-sm text-muted-foreground">
                Encontre rapidamente qualquer momento da reunião buscando por
                palavras ou frases específicas.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Clock className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Timestamps Precisos
              </h3>
              <p className="text-sm text-muted-foreground">
                Navegue pela transcrição e clique em qualquer trecho para ir
                direto ao momento no vídeo.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-lg border border-border bg-background">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Identificação de Speakers
              </h3>
              <p className="text-sm text-muted-foreground">
                Identifica quem está falando em cada momento para facilitar a
                leitura da transcrição.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-semibold tracking-tight mb-4">
              Como funciona
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Em 3 passos simples você terá todas as suas reuniões documentadas.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="relative">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-display font-semibold">
                  1
                </div>
                <div className="hidden md:block flex-1 h-px bg-border" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Conecte seu calendário
              </h3>
              <p className="text-sm text-muted-foreground">
                Faça login com sua conta Google e autorize o acesso ao seu
                calendário. Suas reuniões aparecerão automaticamente.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-display font-semibold">
                  2
                </div>
                <div className="hidden md:block flex-1 h-px bg-border" />
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                O bot entra automaticamente
              </h3>
              <p className="text-sm text-muted-foreground">
                Quando sua reunião começar, o RKJ.AI entra automaticamente e
                começa a gravar. Você não precisa fazer nada.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="flex items-center gap-4 mb-4">
                <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-display font-semibold">
                  3
                </div>
              </div>
              <h3 className="font-display text-lg font-semibold mb-2">
                Acesse gravação e transcrição
              </h3>
              <p className="text-sm text-muted-foreground">
                Após a reunião, você encontra a gravação e a transcrição
                completa no seu dashboard.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-card border-t border-border">
        <div className="mx-auto max-w-6xl px-6">
          <div className="max-w-2xl mx-auto text-center space-y-6">
            <h2 className="font-display text-3xl md:text-4xl font-semibold tracking-tight">
              Pronto para documentar suas reuniões?
            </h2>
            <p className="text-muted-foreground">
              Comece agora e nunca mais perca informações importantes das suas
              reuniões.
            </p>
            <Button asChild size="lg" className="min-w-[200px]">
              <Link href={user ? "/dashboard" : "/login"}>
                {user ? "Acessar Dashboard" : "Criar Conta Grátis"}
                <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}
