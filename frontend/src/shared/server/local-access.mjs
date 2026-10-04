/** Keep the same-host API proxy local before it rewrites the backend Host. */
export function isLocalHost(host) {
  if (!host || /[\/@?#]/.test(host)) return false;
  try {
    const url = new URL(`http://${host}`);
    return ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
  } catch {
    return false;
  }
}
