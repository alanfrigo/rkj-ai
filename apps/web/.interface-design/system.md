# Design System: Executive Briefing Room

Meeting Assistant (RKJ.AI) - Assistente de reuniões com gravação e transcrição automática.

## Direction

**Conceito:** Uma sala de reuniões premium — profissional, confiável, discreto. Materiais nobres mas não ostensivos. O usuário é um profissional ocupado que precisa encontrar informações rapidamente entre calls.

**Feel:** Como um assistente executivo competente que antecipa suas necessidades. Warm, mas não amigável demais. Professional, mas não frio.

## Typography

- **Display:** Fraunces (serifa variável, elegante, para títulos e números grandes)
- **UI:** Instrument Sans (geométrica limpa com personalidade)
- **Mono:** JetBrains Mono (para dados e timestamps)

## Color Palette

### Primitives

**Warm Neutrals (Cream)**
- `--cream-50`: #FDFBF7 (background light)
- `--cream-100`: #F8F6F1 (card light)
- `--cream-200`: #F0EDE5 (muted/secondary)
- `--cream-300`: #E8E4DC (border)
- `--cream-600`: #968E7D (muted foreground)
- `--cream-900`: #2D2A24 (foreground)
- `--cream-950`: #1A1815 (background dark)

**Terracotta (Primary)**
- `--terracotta-400`: #E2856A (dark mode primary)
- `--terracotta-500`: #C4704B (light mode primary)
- `--terracotta-600`: #A85A3A (hover)

**Amber (Active/Warning)**
- `--amber-400`: #FBBF24
- `--amber-500`: #D4A853

**Sage (Success)**
- `--sage-400`: #7D8B74
- `--sage-500`: #5F7158

**Slate (Info)**
- `--slate-500`: #64748B

**Rose (Destructive)**
- `--rose-500`: #F43F5E

## Depth Strategy

**Borders-only** — Clean, minimal. Hierarquia vem da cor das superfícies, não de elevação com sombras.

- Cards usam `border border-border bg-card`
- Sem sombras dramáticas
- Hover states mudam para `bg-accent/50`

## Spacing

Base: 4px (Tailwind default)
- Padding em cards: `p-4` a `p-6`
- Gap entre seções: `space-y-6` a `space-y-8`
- Gap entre items de lista: `divide-y divide-border`

## Border Radius

Refinado, não muito arredondado:
- `--radius-sm`: 0.375rem (6px) - badges, small elements
- `--radius`: 0.5rem (8px) - buttons, inputs
- `--radius-lg`: 0.75rem (12px) - cards
- `--radius-xl`: 1rem (16px) - modals

## Layout Patterns

### Dashboard (Briefing Hero)
- Header com saudação + stats inline (não em cards separados)
- Próxima reunião como hero card com timeline-ribbon no topo
- Grid 3:2 (conteúdo principal : painel lateral)
- Listas usam `divide-y` em vez de cards separados

### Lista de Reuniões (Dense Table)
- Agrupamento por período (Hoje, Ontem, Esta semana, Mês)
- Tabela densa com colunas: Status | Título | Horário | Duração | Participantes
- Headers de grupo com linha separadora: `texto --- count`
- Hover row com `bg-accent/50`

### Meeting Detail (Side-by-Side)
- Grid 1:1 em desktop (video | transcrição)
- Transcrição com altura fixa e scroll interno
- Segmentos com avatar + timestamp + texto
- Footer com ação de copiar

### Settings (Sections)
- Seções com header uppercase muted
- Cards com `divide-y` para items relacionados
- Largura máxima `max-w-2xl` para legibilidade

### Sidebar
- Largura: `w-56` (compacta)
- Logo menor: `h-7 w-7`
- Nav items com `space-y-0.5`
- Footer com theme toggle + logout

## Components

### Button
- Variantes: default (terracotta), outline, ghost, secondary, destructive, success
- Tamanhos: sm (h-9), default (h-10), lg (h-11), icon (h-10 w-10)
- Sem sombras, transições suaves

### Card
- `rounded-lg border border-border bg-card`
- Sem variantes de elevação
- Headers com `border-b` quando necessário

### Badge
- `rounded-md px-2 py-0.5 text-xs`
- Cores semânticas: completed (sage), recording (rose pulse), scheduled (slate), processing (amber pulse)

### Avatar
- Tamanhos: xs (h-6), sm (h-8), md (h-10), lg (h-12)
- Fallback com iniciais em uppercase

## Signature Element

**Timeline Ribbon** — Gradiente de terracotta para amber que aparece em contextos de gravação/transcrição. Representa o "pulso" da reunião.

```css
--ribbon-gradient: linear-gradient(90deg, var(--terracotta-400), var(--amber-400));
--ribbon-glow: 0 0 12px hsla(20, 60%, 55%, 0.25);
```

Uso: No topo do card de próxima reunião, em indicadores de gravação ativa.

## Animation

- Durações rápidas: 150-250ms
- Easing: ease-out
- Sem bouncy/spring effects
- `animate-fade-in`, `animate-slide-up`, `animate-pulse-subtle`

## Default Theme

Light mode como padrão (produtos profissionais tipicamente usam light mode durante horário comercial).

## Key Anti-Patterns (Evitar)

1. **Grid de stat cards genéricos** — use stats inline no header
2. **Cards empilhados para listas** — use `divide-y` dentro de um card
3. **Ícones decorativos em títulos de seção** — use headers uppercase muted
4. **Múltiplos níveis de cards aninhados** — mantenha flat
5. **Botões "Ver todas" óbvios** — use links sutis com chevron
