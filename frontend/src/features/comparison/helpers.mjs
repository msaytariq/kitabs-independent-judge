export function referenceFromHash(hash) {
  const match = /^#(example|scope)=([A-Za-z0-9][A-Za-z0-9_-]{0,79})$/.exec(hash);
  if (match) return {kind:match[1], id:match[2]};
  if (/^#[0-9a-f]{32}$/.test(hash)) return {kind:'legacy', id:hash.slice(1)};
  return null;
}
export function countLabel(value) { return value == null ? 'не оценено' : String(value); }
export function initialMode(hash) { return referenceFromHash(hash)?.kind === 'example' ? 'example' : 'own'; }
