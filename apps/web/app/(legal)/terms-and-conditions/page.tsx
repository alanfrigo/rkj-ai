import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Termos de Serviço | RKJ.AI",
  description:
    "Termos de Serviço do RKJ.AI - Condições de uso do nosso assistente de reuniões.",
};

export default function TermsAndConditionsPage() {
  return (
    <article className="prose prose-slate max-w-none dark:prose-invert">
      <header className="mb-12 border-b border-border pb-8">
        <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground">
          Termos de Serviço
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Última atualização: {new Date().toLocaleDateString("pt-BR")}
        </p>
      </header>

      <section className="space-y-8">
        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            1. Aceitação dos Termos
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Ao acessar ou usar o serviço RKJ.AI (&quot;Serviço&quot;), você
            concorda em ficar vinculado a estes Termos de Serviço
            (&quot;Termos&quot;). Se você não concorda com qualquer parte destes
            termos, não poderá acessar o Serviço.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Estes Termos se aplicam a todos os visitantes, usuários e outras
            pessoas que acessam ou usam o Serviço. Ao usar o Serviço, você
            também concorda com nossa{" "}
            <a
              href="/privacy-policy"
              className="text-primary underline hover:text-primary/80"
            >
              Política de Privacidade
            </a>
            .
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            2. Descrição do Serviço
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            O RKJ.AI é uma plataforma de assistente de reuniões que oferece:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Sincronização com seu Google Calendar para identificar reuniões
            </li>
            <li>
              Participação automatizada em reuniões do Google Meet e Zoom
            </li>
            <li>Gravação de áudio e vídeo de reuniões</li>
            <li>
              Transcrição automática do conteúdo das reuniões usando
              inteligência artificial
            </li>
            <li>
              Armazenamento e organização de gravações e transcrições
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            3. Elegibilidade
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Para usar o Serviço, você deve:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Ter pelo menos 18 anos de idade</li>
            <li>
              Ter capacidade legal para celebrar um contrato vinculativo
            </li>
            <li>
              Não estar impedido de usar o Serviço sob as leis aplicáveis
            </li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Ao usar o Serviço, você declara e garante que atende a todos os
            requisitos de elegibilidade acima.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            4. Sua Conta
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Ao criar uma conta conosco, você deve fornecer informações precisas,
            completas e atualizadas. O não cumprimento dessa obrigação constitui
            uma violação dos Termos.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você é responsável por:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Manter a confidencialidade de sua senha e credenciais de acesso
            </li>
            <li>
              Todas as atividades que ocorram sob sua conta
            </li>
            <li>
              Notificar-nos imediatamente sobre qualquer uso não autorizado de
              sua conta
            </li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Não seremos responsáveis por quaisquer perdas ou danos decorrentes
            do não cumprimento das obrigações de segurança acima.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            5. Uso Aceitável
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você concorda em usar o Serviço apenas para fins legais e de acordo
            com estes Termos. Você concorda em não:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Gravar reuniões sem o conhecimento e consentimento de todos os
              participantes, quando exigido por lei
            </li>
            <li>
              Usar o Serviço para qualquer propósito ilegal ou não autorizado
            </li>
            <li>
              Tentar obter acesso não autorizado a qualquer parte do Serviço
            </li>
            <li>
              Usar o Serviço de forma que possa danificar, desabilitar,
              sobrecarregar ou prejudicar nossos servidores
            </li>
            <li>
              Interferir no uso e aproveitamento do Serviço por outros usuários
            </li>
            <li>
              Coletar ou armazenar dados pessoais de outros usuários sem seu
              consentimento
            </li>
            <li>
              Usar o Serviço para transmitir material ofensivo, difamatório,
              obsceno ou ilegal
            </li>
            <li>
              Violar direitos de propriedade intelectual de terceiros
            </li>
            <li>
              Contornar ou tentar contornar medidas de segurança do Serviço
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            6. Consentimento para Gravação
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            <strong>Importante:</strong> Você é o único responsável por obter o
            consentimento adequado de todos os participantes antes de gravar
            qualquer reunião. As leis sobre gravação de conversas variam de
            acordo com a jurisdição.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Recomendamos que você:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Informe todos os participantes no início da reunião que ela será
              gravada
            </li>
            <li>
              Obtenha consentimento explícito quando exigido pelas leis locais
            </li>
            <li>
              Consulte um advogado se tiver dúvidas sobre os requisitos legais
              em sua jurisdição
            </li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            O RKJ.AI não se responsabiliza por gravações realizadas sem o
            consentimento apropriado dos participantes.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            7. Propriedade Intelectual
          </h2>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            7.1 Nossos Direitos
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            O Serviço e seu conteúdo original, recursos e funcionalidades são e
            permanecerão propriedade exclusiva da RKJ.AI e seus licenciadores. O
            Serviço é protegido por direitos autorais, marcas comerciais e
            outras leis do Brasil e de outros países.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            7.2 Seu Conteúdo
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Você mantém todos os direitos sobre as gravações e transcrições de
            suas reuniões. Ao usar nosso Serviço, você nos concede uma licença
            limitada para processar, armazenar e exibir seu conteúdo conforme
            necessário para fornecer o Serviço.
          </p>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Você declara e garante que possui os direitos necessários sobre
            qualquer conteúdo que você enviar através do Serviço.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            8. Integrações de Terceiros
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            O Serviço integra-se com plataformas de terceiros, incluindo:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Google Calendar e Google Meet</li>
            <li>Zoom</li>
            <li>OpenAI (para transcrição)</li>
          </ul>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Seu uso dessas integrações está sujeito aos termos de serviço e
            políticas de privacidade dessas plataformas. Não somos responsáveis
            pelas práticas de privacidade ou conteúdo de serviços de terceiros.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            9. Pagamento e Assinatura
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Alguns aspectos do Serviço podem ser oferecidos mediante pagamento.
            Os termos específicos de pagamento, incluindo preços e ciclos de
            cobrança, serão apresentados durante o processo de assinatura.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Reservamo-nos o direito de modificar nossos preços a qualquer
            momento. Qualquer alteração de preço será comunicada com pelo menos
            30 dias de antecedência.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            10. Disponibilidade do Serviço
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Nos esforçamos para manter o Serviço disponível 24 horas por dia, 7
            dias por semana. No entanto, não garantimos que o Serviço estará
            disponível ininterruptamente ou sem erros.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Reservamo-nos o direito de:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Modificar ou descontinuar o Serviço (ou qualquer parte dele) com
              ou sem aviso prévio
            </li>
            <li>
              Realizar manutenção programada ou de emergência
            </li>
            <li>
              Suspender o acesso ao Serviço por razões de segurança ou técnicas
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            11. Limitação de Responsabilidade
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Na extensão máxima permitida pela lei aplicável, em nenhum caso a
            RKJ.AI, seus diretores, funcionários, parceiros, agentes,
            fornecedores ou afiliados serão responsáveis por:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Quaisquer danos indiretos, incidentais, especiais, consequenciais
              ou punitivos
            </li>
            <li>
              Perda de lucros, dados, uso, boa vontade ou outras perdas
              intangíveis
            </li>
            <li>
              Falhas na gravação ou transcrição de reuniões
            </li>
            <li>
              Qualquer acesso não autorizado ou uso de nossos servidores e/ou
              qualquer informação pessoal armazenada neles
            </li>
            <li>
              Qualquer interrupção ou cessação da transmissão para ou do Serviço
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            12. Isenção de Garantias
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            O Serviço é fornecido &quot;como está&quot; e &quot;conforme
            disponível&quot;, sem garantias de qualquer tipo, expressas ou
            implícitas, incluindo, mas não se limitando a, garantias implícitas
            de comercialização, adequação a um propósito específico, não
            violação ou desempenho.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Não garantimos que:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>O Serviço atenderá seus requisitos específicos</li>
            <li>
              O Serviço será ininterrupto, oportuno, seguro ou livre de erros
            </li>
            <li>
              As transcrições serão 100% precisas
            </li>
            <li>
              Os resultados obtidos pelo uso do Serviço serão precisos ou
              confiáveis
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            13. Indenização
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você concorda em defender, indenizar e isentar a RKJ.AI e seus
            licenciadores, funcionários, contratados, agentes, diretores e
            fornecedores de e contra quaisquer reclamações, danos, obrigações,
            perdas, responsabilidades, custos ou dívidas e despesas decorrentes
            de:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>Seu uso e acesso ao Serviço</li>
            <li>Sua violação de qualquer termo destes Termos</li>
            <li>
              Sua violação de direitos de terceiros, incluindo direitos de
              privacidade
            </li>
            <li>
              Qualquer reclamação de que seu uso do Serviço causou danos a
              terceiros
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            14. Rescisão
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Podemos encerrar ou suspender sua conta e acesso ao Serviço
            imediatamente, sem aviso prévio ou responsabilidade, por qualquer
            motivo, incluindo, sem limitação, se você violar os Termos.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Você pode encerrar sua conta a qualquer momento através das
            configurações do seu perfil. Após a rescisão:
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              Seu direito de usar o Serviço cessará imediatamente
            </li>
            <li>
              Suas gravações e transcrições serão excluídas após 30 dias, a
              menos que você solicite a exclusão imediata
            </li>
            <li>
              Algumas disposições destes Termos sobreviverão à rescisão
            </li>
          </ul>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            15. Lei Aplicável e Jurisdição
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Estes Termos serão regidos e interpretados de acordo com as leis do
            Brasil, independentemente de seus conflitos de disposições legais.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Qualquer disputa decorrente ou relacionada a estes Termos será
            resolvida exclusivamente nos tribunais competentes da cidade de São
            Paulo, Estado de São Paulo, Brasil.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            16. Alterações nos Termos
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Reservamo-nos o direito, a nosso exclusivo critério, de modificar ou
            substituir estes Termos a qualquer momento. Se uma revisão for
            material, forneceremos pelo menos 30 dias de aviso antes que os
            novos termos entrem em vigor.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Ao continuar a acessar ou usar nosso Serviço após as revisões
            entrarem em vigor, você concorda em ficar vinculado aos termos
            revisados. Se você não concordar com os novos termos, deixe de usar
            o Serviço.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            17. Disposições Gerais
          </h2>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            17.1 Acordo Integral
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Estes Termos constituem o acordo integral entre você e a RKJ.AI
            sobre o uso do Serviço e substituem todos os acordos anteriores.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            17.2 Renúncia
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            A falha da RKJ.AI em exercer ou aplicar qualquer direito ou
            disposição destes Termos não constituirá uma renúncia a esse direito
            ou disposição.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            17.3 Divisibilidade
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Se qualquer disposição destes Termos for considerada inválida ou
            inexequível, as disposições restantes permanecerão em pleno vigor e
            efeito.
          </p>

          <h3 className="mt-6 text-xl font-medium text-foreground">
            17.4 Cessão
          </h3>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Você não pode ceder ou transferir estes Termos sem nosso
            consentimento prévio por escrito. Podemos ceder nossos direitos e
            obrigações a qualquer momento.
          </p>
        </div>

        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            18. Contato
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Se você tiver dúvidas sobre estes Termos de Serviço, entre em
            contato conosco:
          </p>
          <div className="mt-4 rounded-lg border border-border bg-card p-6">
            <p className="font-medium text-foreground">RKJ.AI</p>
            <p className="mt-2 text-muted-foreground">
              E-mail:{" "}
              <a
                href="mailto:suporte@rkj.ai"
                className="text-primary underline hover:text-primary/80"
              >
                suporte@rkj.ai
              </a>
            </p>
          </div>
        </div>
      </section>
    </article>
  );
}
