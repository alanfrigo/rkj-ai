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
- Hover states mudam borda para `border-cream-400`

## Spacing

Base: 4px (Tailwind default)
- Padding em cards: `p-6`
- Gap entre seções: `space-y-8`
- Gap entre items: `space-y-2` ou `space-y-1`

## Border Radius

Refinado, não muito arredondado:
- `--radius-sm`: 0.375rem (6px) - badges, small elements
- `--radius`: 0.5rem (8px) - buttons, inputs
- `--radius-lg`: 0.75rem (12px) - cards
- `--radius-xl`: 1rem (16px) - modals

## Components

### Button
- Variantes: default (terracotta), outline, ghost, secondary, destructive, success
- Tamanhos: sm (h-9), default (h-10), lg (h-11), icon (h-10 w-10)
- Sem sombras, transições suaves

### Card
- `rounded-lg border border-border bg-card`
- Sem variantes de elevação
- Hover com `hover:border-cream-400`

### Badge
- `rounded-md px-2 py-0.5 text-xs`
- Cores semânticas: completed (sage), recording (rose pulse), scheduled (slate), processing (amber pulse)

### Sidebar
- Largura: `w-60`
- Logo: Mic icon + "RKJ.AI" em Fraunces
- Nav items: texto com ícones line-only, 4px
- Active state: `bg-primary/10 text-primary`

## Signature Element

**Timeline Ribbon** — Gradiente de terracotta para amber que aparece em contextos de gravação/transcrição. Representa o "pulso" da reunião.

```css
--ribbon-gradient: linear-gradient(90deg, var(--terracotta-400), var(--amber-400));
--ribbon-glow: 0 0 12px hsla(20, 60%, 55%, 0.25);
```

## Animation

- Durações rápidas: 150-250ms
- Easing: ease-out
- Sem bouncy/spring effects
- `animate-fade-in`, `animate-slide-up`, `animate-pulse-subtle`

## Default Theme

Light mode como padrão (produtos profissionais tipicamente usam light mode durante horário comercial).

## Key Patterns

1. **Stats Cards:** Número grande em Fraunces + ícone em background colorido sutil
2. **List Items:** Hover com `bg-accent`, ícone à esquerda, badge à direita
3. **Empty States:** Ícone centralizado + texto muted
4. **Alerts:** Border colorida sutil + background 5% da cor
