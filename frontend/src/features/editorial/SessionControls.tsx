"use client";
import { useEffect, useState } from "react";
import type { Command, Review, Side } from "../../shared/types/editorial";
import { elapsedSeconds } from "./helpers.mjs";
export function SessionControls({
  review,
  command,
  busy,
  actor,
}: {
  review: Review;
  command: Command;
  busy: boolean;
  actor: string;
}) {
  const [side, setSide] = useState<Side>("a"),
    [stage, setStage] = useState("editing"),
    [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const active = review.sessions.find((s) => s.status !== "stopped");
  return (
    <section className="panel timer">
      <div>
        <span className="eyebrow">02 · Record your work</span>
        <h2>
          {active
            ? `${active.status === "paused" ? "Paused" : "Working"} on version ${active.side.toUpperCase()}`
            : "Start an editorial session"}
        </h2>
        <p className="muted">
          Pause during breaks. Closing this page does not stop the timer.
        </p>
      </div>
      {active ? (
        <>
          <div className="clock">
            {Math.floor(elapsedSeconds(active, now))} <small>seconds</small>
            <span>
              {active.stage} · {active.actor}
            </span>
          </div>
          <div className="actions">
            <button
              disabled={busy || actor !== active.actor}
              onClick={() =>
                void command(
                  active.status === "paused" ? "resume" : "pause",
                  {},
                )
              }
            >
              {active.status === "paused" ? "Resume" : "Pause"}
            </button>
            <button
              disabled={busy || actor !== active.actor}
              onClick={() => void command("stop", {})}
            >
              Stop session
            </button>
          </div>
        </>
      ) : (
        <div className="row">
          <label>
            Version
            <select
              value={side}
              onChange={(e) => setSide(e.target.value as Side)}
            >
              <option value="a">A</option>
              <option value="b">B</option>
            </select>
          </label>
          <label>
            Activity
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="editing">Editing / research</option>
              <option value="verification">Final verification</option>
            </select>
          </label>
          <button
            className="primary"
            disabled={busy || !actor.trim()}
            onClick={() => void command("start", { side, stage })}
          >
            Start timer
          </button>
        </div>
      )}
    </section>
  );
}
