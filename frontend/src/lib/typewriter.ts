/**
 * Typing effect for rendered content. The markdown is rendered ONCE; this reveals the
 * text nodes of the already-rendered element a few characters at a time, so formatting
 * never flickers and nothing is parsed again per character.
 *
 * Returns a cancel function that shows the full text immediately.
 */
export function typeInto(
  element: HTMLElement,
  options: { charsPerTick?: number; tickMs?: number; onProgress?: () => void } = {},
): () => void {
  const { charsPerTick = 4, tickMs = 15, onProgress } = options;

  const nodes: { node: Text; full: string }[] = [];
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode as Text;
    nodes.push({ node, full: node.textContent ?? '' });
    node.textContent = '';
  }

  let index = 0;
  let shown = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const step = () => {
    let budget = charsPerTick;
    while (budget > 0 && index < nodes.length) {
      const entry = nodes[index];
      if (!entry) break;
      const take = Math.min(budget, entry.full.length - shown);
      shown += take;
      budget -= take;
      entry.node.textContent = entry.full.slice(0, shown);
      if (shown >= entry.full.length) {
        index += 1;
        shown = 0;
      }
    }
    onProgress?.();
    if (index < nodes.length) timer = setTimeout(step, tickMs);
  };
  step();

  return () => {
    if (timer !== undefined) clearTimeout(timer);
    for (const { node, full } of nodes) node.textContent = full;
  };
}
