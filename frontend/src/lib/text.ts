/** Strips the most common markdown so a stored answer reads as plain text in a short preview. */
export function plainText(markdown: string): string {
  return markdown
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1') // links and images -> their text
    .replace(/(\*\*|__|\*|_|`)/g, '') // emphasis and code marks
    .replace(/^\s{0,3}(#{1,6}|[-*+]|\d+\.)\s+/gm, '') // headings and list markers
    .replace(/\s+/g, ' ')
    .trim();
}
