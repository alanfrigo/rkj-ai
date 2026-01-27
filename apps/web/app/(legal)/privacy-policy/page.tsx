import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidade | RKJ.AI",
  description:
    "Política de Privacidade do RKJ.AI - Saiba como coletamos, usamos e protegemos seus dados.",
};

export default function PrivacyPolicyPage() {
  return (
    <article className="prose prose-slate max-w-none dark:prose-invert">
      <header className="mb-12 border-b border-border pb-8">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground">
          Política de Privacidade
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Última atualização: {new Date().toLocaleDateString("pt-BR")}
        </p>
      </header>

      <section className="space-y-8">
        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            1. Introdução
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            A RKJ.AI (&quot;nós&quot;, &quot;nosso&quot; ou &quot;empresa&quot;)
            está comprometida em proteger a privacidade dos usuários de nosso
            serviço de assistente de reuniões. Esta Política de Privacidade
            explica como coletamos, usamos, divulgamos e protegemos suas
            informações quando você utiliza nossa plataforma.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Ao usar o RKJ.AI, você concorda com a coleta e uso de informações de
            acordo com esta política. Recomendamos que você leia este documento
            com atenção.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            2. Informações que Coletamos
          </h2>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            2.1 Informações da Conta
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Quando você cria uma conta, coletamos:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Nome completo</li>
            <li>Endereço de e-mail</li>
            <li>Foto de perfil (quando fornecida via Google)</li>
            <li>Informações de autenticação</li>
          </ul>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            2.2 Dados do Google Calendar
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Com sua permissão explícita, acessamos:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Eventos do calendário que contêm links de reunião (Google Meet ou
              Zoom)
            </li>
            <li>Títulos e descrições das reuniões</li>
            <li>Horários de início e término</li>
            <li>Lista de participantes</li>
          </ul>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            <strong>Importante:</strong> Acessamos apenas os dados necessários
            para identificar e participar de reuniões. Não modificamos, criamos
            ou deletamos eventos em seu calendário.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            2.3 Dados de Reuniões
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Durante a utilização do serviço, coletamos:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Gravações de áudio e vídeo das reuniões que você solicitar</li>
            <li>Transcrições geradas a partir das gravações</li>
            <li>Metadados das reuniões (duração, participantes, horários)</li>
          </ul>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            2.4 Dados de Uso
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Coletamos automaticamente informações sobre como você interage com
            nosso serviço:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Logs de acesso e endereço IP</li>
            <li>Tipo de navegador e dispositivo</li>
            <li>Páginas visitadas e funcionalidades utilizadas</li>
            <li>Horários de acesso</li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            3. Como Usamos Suas Informações
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Utilizamos as informações coletadas para:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Fornecer, manter e melhorar nossos serviços</li>
            <li>
              Identificar reuniões em seu calendário e participar delas conforme
              solicitado
            </li>
            <li>
              Gravar e transcrever reuniões de acordo com suas configurações
            </li>
            <li>Enviar notificações sobre suas reuniões e gravações</li>
            <li>
              Responder a suas solicitações de suporte e comunicações
            </li>
            <li>Detectar, prevenir e resolver problemas técnicos</li>
            <li>Cumprir obrigações legais</li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            4. Compartilhamento de Informações
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Não vendemos, alugamos ou compartilhamos suas informações pessoais
            com terceiros para fins de marketing. Podemos compartilhar suas
            informações apenas nas seguintes circunstâncias:
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            4.1 Provedores de Serviço
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Compartilhamos dados com provedores terceirizados que nos ajudam a
            operar o serviço:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <strong>OpenAI:</strong> Para transcrição de áudio usando a API
              Whisper. Os arquivos de áudio são processados e não são retidos
              pela OpenAI após o processamento.
            </li>
            <li>
              <strong>Cloudflare R2:</strong> Para armazenamento seguro de
              gravações.
            </li>
            <li>
              <strong>Supabase:</strong> Para autenticação e armazenamento de
              dados.
            </li>
          </ul>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            4.2 Requisitos Legais
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Podemos divulgar suas informações se exigido por lei, processo
            legal, ou solicitação governamental, ou quando acreditarmos de
            boa-fé que a divulgação é necessária para proteger nossos direitos,
            sua segurança ou a segurança de terceiros.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            4.3 Transferência de Negócios
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Em caso de fusão, aquisição ou venda de ativos, suas informações
            podem ser transferidas. Notificaremos você sobre qualquer mudança na
            propriedade ou no uso de suas informações.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            5. Uso de Dados do Google
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            O uso de informações recebidas das APIs do Google está em
            conformidade com a{" "}
            <a
              href="https://developers.google.com/terms/api-services-user-data-policy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline hover:text-primary/80"
            >
              Política de Dados do Usuário dos Serviços de API do Google
            </a>
            , incluindo os requisitos de Uso Limitado.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Especificamente:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Usamos os dados do Google Calendar exclusivamente para identificar
              reuniões e fornecer nosso serviço de gravação
            </li>
            <li>
              Não transferimos dados do Google para terceiros, exceto conforme
              necessário para fornecer o serviço
            </li>
            <li>
              Não usamos dados do Google para publicidade ou criação de perfis
              de usuário
            </li>
            <li>
              Você pode revogar nosso acesso a qualquer momento nas
              configurações de sua conta Google
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            6. Armazenamento e Segurança de Dados
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Implementamos medidas de segurança técnicas e organizacionais para
            proteger suas informações:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Criptografia de dados em trânsito (TLS/SSL)</li>
            <li>Criptografia de dados em repouso</li>
            <li>Acesso restrito a dados pessoais por funcionários autorizados</li>
            <li>Monitoramento contínuo de segurança</li>
            <li>Backups regulares e planos de recuperação de desastres</li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            <strong>Retenção de Dados:</strong> Mantemos suas gravações e
            transcrições enquanto sua conta estiver ativa ou conforme necessário
            para fornecer o serviço. Você pode excluir suas gravações a qualquer
            momento através do painel de controle.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            7. Seus Direitos
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você tem os seguintes direitos em relação aos seus dados pessoais:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <strong>Acesso:</strong> Solicitar uma cópia dos dados que temos
              sobre você
            </li>
            <li>
              <strong>Correção:</strong> Solicitar a correção de dados imprecisos
            </li>
            <li>
              <strong>Exclusão:</strong> Solicitar a exclusão de seus dados
              pessoais
            </li>
            <li>
              <strong>Portabilidade:</strong> Receber seus dados em formato
              estruturado
            </li>
            <li>
              <strong>Revogação:</strong> Revogar o consentimento para o
              processamento de dados
            </li>
            <li>
              <strong>Objeção:</strong> Opor-se ao processamento de seus dados em
              certas circunstâncias
            </li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Para exercer qualquer desses direitos, entre em contato conosco
            através do e-mail fornecido na seção de Contato.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            8. Cookies e Tecnologias de Rastreamento
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Utilizamos cookies e tecnologias similares para:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Manter você conectado à sua conta</li>
            <li>Lembrar suas preferências</li>
            <li>Entender como você usa nosso serviço</li>
            <li>Melhorar a segurança</li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você pode configurar seu navegador para recusar cookies, mas isso
            pode afetar a funcionalidade do serviço.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            9. Privacidade de Menores
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Nosso serviço não é direcionado a menores de 18 anos. Não coletamos
            intencionalmente informações de menores. Se você é pai ou
            responsável e acredita que seu filho nos forneceu informações
            pessoais, entre em contato conosco.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            10. Transferências Internacionais de Dados
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Seus dados podem ser transferidos e processados em servidores
            localizados fora do seu país de residência. Tomamos medidas para
            garantir que suas informações recebam um nível adequado de proteção
            onde quer que sejam processadas.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            11. Alterações nesta Política
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Podemos atualizar esta Política de Privacidade periodicamente.
            Notificaremos você sobre quaisquer alterações publicando a nova
            política nesta página e atualizando a data de &quot;última
            atualização&quot;. Para alterações materiais, enviaremos uma
            notificação por e-mail.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Recomendamos que você revise esta política periodicamente para se
            manter informado sobre como protegemos suas informações.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            12. Contato
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Se você tiver dúvidas sobre esta Política de Privacidade ou sobre
            nossas práticas de privacidade, entre em contato conosco:
          </p>
          <div className="mt-4 rounded-lg border border-border bg-card p-6">
            <p className="font-medium text-foreground">RKJ.AI</p>
            <p className="mt-2 text-muted-foreground">
              E-mail:{" "}
              <a
                href="mailto:privacidade@rkj.ai"
                className="text-primary underline hover:text-primary/80"
              >
                privacidade@rkj.ai
              </a>
            </p>
          </div>
        </div>
      </section>
    </article>
  );
}
