# SVDA design system

[Leia em português](design-system.pt-BR.md)

The visual identity is called **Pasto** (pasture). It is built around one idea from the producer's world: the contour lines ("curvas de nível") of a farm map. The tokens live in [`frontend/src/styles/index.css`](../../frontend/src/styles/index.css) (Tailwind `@theme`).

## Palette

| Token                | Hex       | Use                                              |
| -------------------- | --------- | ------------------------------------------------ |
| `field`              | `#EFF4E9` | Page background                                  |
| `ink`                | `#1B2A21` | Body text                                        |
| `muted`              | `#55665B` | Secondary text                                   |
| `line`               | `#C9D6C2` | Field borders                                    |
| `moss` / `moss-light`| `#22402E` / `#2C5039` | Brand color, sidebar, primary actions |
| `grass`              | `#5F8F46` | Accents and contour lines                        |
| `sun`                | `#F2B84B` | Highlights, "new conversation", send button      |
| `sky`                | `#DCEAEE` | Chips and notices                                |
| `mist`               | `#B9CDB9` | Secondary text on the dark sidebar               |

## Typography

- **Display** (SVDA wordmark, headings): Bricolage Grotesque, variable weight.
- **Text** (interface, messages): Figtree 400 / 500 / 600 / 700.

Both ship with the app through `@fontsource` packages (SIL Open Font License); nothing is loaded from third-party servers.

## Signature

- Contour lines as the page and sidebar background, generated from code (`frontend/src/lib/contour.ts`).
- Every conversation gets its own small "terrain" thumbnail, drawn from its id, so conversations are recognizable at a glance.

## Responsive behavior

| Width            | Layout                                                           |
| ---------------- | ---------------------------------------------------------------- |
| below 768 px     | One pane at a time: conversation list, then chat with a back button |
| 768 px and above | List and chat side by side                                       |

## Accessibility and comfort

- Interactive targets are at least 48 px; inputs are 16 px, so iOS does not zoom.
- Visible keyboard focus on every control (moss on light areas, sun on the dark sidebar).
- Respects `prefers-reduced-motion` (no typing effect or animations).
- Uses `dvh` units and safe-area insets so mobile browser bars and notches do not cover the composer.
- The disclaimer that answers do not replace a veterinarian is always visible in the chat.

The original (2025) visual guide is kept in [`legacy-visual-guide.pdf`](legacy-visual-guide.pdf) and the notes next to it, for reference only.
