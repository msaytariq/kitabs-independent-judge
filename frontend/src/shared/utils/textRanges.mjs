/** Python range endpoints count Unicode code points, not UTF-16 code units. */
export function fullRanges(materials) {
  return Object.fromEntries(Object.entries(materials).map(([role, m]) =>
    [role, {start:0, end:Array.from(m.text).length, text_sha256:m.sha256}]));
}
