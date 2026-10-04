import test from "node:test";
import assert from "node:assert/strict";
import { isLocalHost } from "../src/shared/server/local-access.mjs";
test("Only loopback hosts can reach the browser proxy, including GET requests", () => {
  for (const host of ["127.0.0.1:3005", "localhost:3005", "[::1]:3005"])
    assert.equal(isLocalHost(host), true);
  for (const host of [
    null,
    "",
    "evil.example:3005",
    "127.0.0.1.evil.example",
    "evil@localhost:3005",
    "localhost/evil",
  ])
    assert.equal(isLocalHost(host), false);
});
