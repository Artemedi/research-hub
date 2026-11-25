export function withoutFencedCode(text) {
  let fence = null;
  return text.split(/\r?\n/).map(line => {
    const marker = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
    if (fence) {
      if (marker && marker[1][0] === fence[0] && marker[1].length >= fence.length && !marker[2].trim()) fence = null;
      return '';
    }
    if (marker && (marker[1][0] === '~' || !marker[2].includes('`'))) {
      fence = marker[1];
      return '';
    }
    return line;
  }).join('\n');
}

export function slug(s) { return s.trim().toLowerCase().replace(/<[^>]*>/g, '').replace(/[^\p{L}\p{N}\p{M}_\-\s]/gu, '').replace(/ /g, '-'); }
export function markdownHeadings(text) {
  const headings = [];
  const used = new Map();
  const lines = text.split(/\r?\n/);
  for (const [line, content] of lines.entries()) {
    const heading = /^#{1,6} (.+)$/.exec(content);
    if (!heading) continue;
    const base = slug(heading[1]);
    const count = used.get(base) ?? 0;
    used.set(base, count + 1);
    headings.push({ id: base + (count ? `-${count}` : ''), line });
  }
  return headings;
}

export function markdownAnchors(text, headings = markdownHeadings(text)) {
  const anchors = new Set(headings.map(item => item.id));
  for (const match of text.matchAll(/<a\s+(?:id|name)="([^"]+)"/g)) anchors.add(match[1]);
  return anchors;
}
