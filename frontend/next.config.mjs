const backend = process.env.JUDGE_API_ORIGIN || "http://127.0.0.1:8765";
const url = new URL(backend);
if (!["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)) {
  throw new Error("The local workbench requires a loopback backend.");
}
export default {
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${url.origin}/api/:path*` }];
  },
};
