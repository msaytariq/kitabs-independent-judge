#!/bin/sh
# Build the public Judge screen as static files under a path prefix.
# Usage: scripts/build_public_frontend.sh /judge <output-directory> [commit]
# The files come from the commit (default HEAD), never from uncommitted work.
# The local stand keeps its loopback-only middleware; the public copy has none,
# because the web server in front of it is the access boundary.
set -eu
base="$1"; out="$2"; commit="${3:-HEAD}"
root=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git -C "$root" archive "$commit" frontend | tar -x -C "$work" --strip-components=1
rm -rf "$work/middleware.ts" "$work/app/editorial"
ln -s "$root/frontend/node_modules" "$work/node_modules"
(cd "$work" && NEXT_TELEMETRY_DISABLED=1 JUDGE_PUBLIC_BASE_PATH="$base" npx next build)
rm -rf "$out"; mkdir -p "$out"
cp -R "$work/out/." "$out/"
git -C "$root" rev-parse "$commit" > "$out/COMMIT"
echo "Public screen: $out (base path $base, commit $(cat "$out/COMMIT"))"
