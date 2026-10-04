export function codePointRange(text, start, end) {
  for (const n of [start, end]) {
    if (!Number.isInteger(n) || n < 0 || n > text.length)
      throw new Error("Invalid text selection");
    const previous = text.charCodeAt(n - 1),
      next = text.charCodeAt(n);
    if (
      previous >= 0xd800 &&
      previous <= 0xdbff &&
      next >= 0xdc00 &&
      next <= 0xdfff
    )
      throw new Error("Selection splits a Unicode character");
  }
  if (start > end) throw new Error("Invalid selection order");
  return {
    start: Array.from(text.slice(0, start)).length,
    end: Array.from(text.slice(0, end)).length,
  };
}
export function formatSeconds(value) {
  if (value === null) return "Unknown";
  return value < 60
    ? `${value.toFixed(1)} sec`
    : `${(value / 60).toFixed(1)} min`;
}
export function elapsedSeconds(session, now) {
  return (
    session.intervals.reduce(
      (sum, i) => sum + Math.max(0, (i.end_ms ?? now) - i.start_ms),
      0,
    ) / 1000
  );
}
