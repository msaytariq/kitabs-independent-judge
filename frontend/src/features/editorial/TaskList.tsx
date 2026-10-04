"use client";
import { useState } from "react";
import type { Command, Side, Task } from "../../shared/types/editorial";
function TaskCard({
  task,
  side,
  version,
  sha,
  command,
  busy,
}: {
  task: Task;
  side: Side;
  version: number;
  sha: string;
  command: Command;
  busy: boolean;
}) {
  const [reason, setReason] = useState("");
  const status = task.decision
    ? task.decision.version === version
      ? task.decision.status
      : "needs recheck"
    : "open";
  return (
    <article className="task">
      <span className="badge">
        {task.category} · {status}
      </span>
      <h4>{task.title}</h4>
      <blockquote dir="auto">{task.anchor.quote}</blockquote>
      <p className="muted">
        Anchor: version {task.anchor.version}.{" "}
        {task.decision && `Last decision: ${task.decision.reason}`}
      </p>
      <label>
        Decision explanation
        <input value={reason} onChange={(e) => setReason(e.target.value)} />
      </label>
      <div className="actions">
        {(["confirmed", "resolved", "dismissed"] as const).map((s) => (
          <button
            key={s}
            disabled={busy || !reason.trim()}
            onClick={() =>
              void command("decide_task", {
                side,
                task_id: task.id,
                status: s,
                reason,
                expected_sha256: sha,
              })
            }
          >
            {s === "confirmed"
              ? "Confirm task"
              : s === "resolved"
                ? "Mark resolved"
                : "Dismiss finding"}
          </button>
        ))}
      </div>
    </article>
  );
}
export function TaskList(props: {
  tasks: Task[];
  side: Side;
  version: number;
  sha: string;
  command: Command;
  busy: boolean;
}) {
  return (
    <div>
      <h3>
        Editorial tasks <span className="muted">({props.tasks.length})</span>
      </h3>
      {props.tasks.length ? (
        props.tasks.map((task) => (
          <TaskCard key={task.id} {...props} task={task} />
        ))
      ) : (
        <p className="muted">
          No tasks recorded. This does not certify the absence of errors. Select
          text above to add a task.
        </p>
      )}
    </div>
  );
}
