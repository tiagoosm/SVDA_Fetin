# Sistema de design do SVDA

[Read in English](design-system.md)

A identidade visual se chama **Pasto**. Ela se constrói em torno de uma ideia do mundo do produtor: as curvas de nível de um mapa de fazenda. Os tokens ficam em [`frontend/src/styles/index.css`](../../frontend/src/styles/index.css) (`@theme` do Tailwind).

## Paleta

| Token                | Hex       | Uso                                                |
| -------------------- | --------- | -------------------------------------------------- |
| `field`              | `#EFF4E9` | Fundo da página                                    |
| `ink`                | `#1B2A21` | Texto                                              |
| `muted`              | `#55665B` | Texto secundário                                   |
| `line`               | `#C9D6C2` | Bordas dos campos                                  |
| `moss` / `moss-light`| `#22402E` / `#2C5039` | Cor da marca, barra lateral, ações principais |
| `grass`              | `#5F8F46` | Detalhes e curvas de nível                         |
| `sun`                | `#F2B84B` | Destaques, "nova conversa", botão de enviar        |
| `sky`                | `#DCEAEE` | Etiquetas e avisos                                 |
| `mist`               | `#B9CDB9` | Texto secundário sobre a barra lateral escura      |

## Tipografia

- **Display** (marca SVDA, títulos): Bricolage Grotesque, peso variável.
- **Texto** (interface, mensagens): Figtree 400 / 500 / 600 / 700.

As duas vêm junto com o app por pacotes `@fontsource` (licença SIL Open Font); nada é carregado de servidores de terceiros.

## Assinatura

- Curvas de nível como fundo da página e da barra lateral, geradas por código (`frontend/src/lib/contour.ts`).
- Cada conversa ganha uma miniatura de "terreno" própria, desenhada a partir do seu id, para reconhecê-la de relance.

## Comportamento responsivo

| Largura            | Layout                                                              |
| ------------------ | ------------------------------------------------------------------- |
| abaixo de 768 px   | Um painel por vez: lista de conversas, depois chat com botão de voltar |
| 768 px ou mais     | Lista e chat lado a lado                                            |

## Acessibilidade e conforto

- Alvos de toque de pelo menos 48 px; campos de 16 px, para o iOS não dar zoom.
- Foco visível por teclado em todos os controles (musgo em áreas claras, amarelo na barra escura).
- Respeita `prefers-reduced-motion` (sem efeito de digitação nem animações).
- Usa unidades `dvh` e áreas seguras, para barras do navegador e entalhes do celular não cobrirem o campo de mensagem.
- O aviso de que as respostas não substituem um veterinário fica sempre visível no chat.

O guia visual original (2025) continua em [`legacy-visual-guide.pdf`](legacy-visual-guide.pdf), com as notas ao lado, apenas como referência.
