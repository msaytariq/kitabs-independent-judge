import test from "node:test";
import assert from "node:assert/strict";
import {
  codePointRange,
  formatSeconds,
  elapsedSeconds,
} from "../src/features/editorial/helpers.mjs";

test("Arabic and astral symbols keep Python code-point offsets", () => {
  assert.deepEqual(codePointRange("أ😀ب", 1, 3), { start: 1, end: 2 });
  assert.deepEqual(codePointRange("أ😀ب", 3, 4), { start: 2, end: 3 });
  assert.throws(() => codePointRange("أ😀ب", 2, 3));
});
test("Unknown effort is not displayed as zero", () => {
  assert.equal(formatSeconds(null), "Unknown");
  assert.equal(formatSeconds(0), "0.0 sec");
  assert.equal(formatSeconds(1.4), "1.4 sec");
  assert.equal(formatSeconds(90), "1.5 min");
});
test("Paused wall time does not inflate the live interval display", () => {
  const intervals = [
    { start_ms: 1000, end_ms: 31000 },
    { start_ms: 100000, end_ms: null },
  ];
  assert.equal(elapsedSeconds({ status: "running", intervals }, 110000), 40);
  assert.equal(
    elapsedSeconds(
      { status: "paused", intervals: [{ start_ms: 1000, end_ms: 31000 }] },
      110000,
    ),
    30,
  );
});
