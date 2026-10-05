// Public build: static files served under JUDGE_PUBLIC_BASE_PATH (for example /judge);
// the web server sends <base>/api/* to the Judge API. Build it with scripts/build_public_frontend.sh.
const base = process.env.JUDGE_PUBLIC_BASE_PATH;
if (base !== undefined && !/^\/[a-z0-9-]+$/.test(base)) {
  throw new Error("JUDGE_PUBLIC_BASE_PATH must look like /judge.");
}

const local = () => {
  const backend = process.env.JUDGE_API_ORIGIN || "http://127.0.0.1:8765";
  const url = new URL(backend);
  if (!["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)) {
    throw new Error("The local workbench requires a loopback backend.");
  }
  return {
    poweredByHeader: false,
    async rewrites() {
      return [{ source: "/api/:path*", destination: `${url.origin}/api/:path*` }];
    },
  };
};

export default base
  ? { output: "export", basePath: base, trailingSlash: true, poweredByHeader: false,
      images: { unoptimized: true }, env: { NEXT_PUBLIC_BASE_PATH: base } }
  : local();
