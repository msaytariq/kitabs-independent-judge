"use client";
import { useEffect, useState } from "react";
import type {
  Command,
  EditorialSide,
  Side,
} from "../../shared/types/editorial";
import { PriorWork } from "./PriorWork";
import { TaskList } from "./TaskList";
import { codePointRange } from "./helpers.mjs";
export function VersionEditor({
  side,
  document,
  command,
  busy,
}: {
  side: Side;
  document: EditorialSide;
  command: Command;
  busy: boolean;
}) {
  const head = document.versions[document.versions.length - 1];
  const [draft, setDraft] = useState(head.text),
    [base, setBase] = useState(head),
    [reason, setReason] = useState("");
  const [range, setRange] = useState({ start: 0, end: 0 }),
    [title, setTitle] = useState(""),
    [category, setCategory] = useState("meaning");
  const [accepted, setAccepted] = useState(false),
    [acceptReason, setAcceptReason] = useState("");
  useEffect(() => {
    if (base.sha256 !== head.sha256 && draft === base.text) {
      setDraft(head.text);
      setBase(head);
      setRange({ start: 0, end: 0 });
    }
  }, [head, base, draft]);
  const dirty = draft !== base.text,
    stale = head.sha256 !== base.sha256;
  async function save() {
    const result = await command("save_version", {
      side,
      text: draft,
      expected_sha256: base.sha256,
      reason,
    });
    if (result) {
      const v = result.sides[side].versions.at(-1)!;
      setBase(v);
      setDraft(v.text);
      setReason("");
      setRange({ start: 0, end: 0 });
    }
  }
  return (
    <section className="panel version">
      <div className="version-heading">
        <h2>Version {side.toUpperCase()}</h2>
        <span className="badge">
          {document.acceptance ? "Accepted" : "Under review"} · v{head.number}
        </span>
      </div>
      <PriorWork
        side={side}
        document={document}
        command={command}
        busy={busy}
      />
      <label>
        Translation · edit or select a passage
        <textarea
          className="translation"
          dir="auto"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onSelect={(e) => {
            const v = e.currentTarget;
            setRange(codePointRange(v.value, v.selectionStart, v.selectionEnd));
          }}
        />
      </label>
      {stale && (
        <p className="error">
          A newer version exists. Your unsaved draft is preserved. Copy it
          before reopening this review.
        </p>
      )}
      <label>
        Reason for this edit
        <input value={reason} onChange={(e) => setReason(e.target.value)} />
      </label>
      <button
        className="primary"
        disabled={busy || !dirty || stale || !reason.trim()}
        onClick={() => void save()}
      >
        Save new version
      </button>
      <p className="muted">
        Saving requires a running editing session. Original versions stay in the
        history.
      </p>
      <details>
        <summary>Add a task from selected text</summary>
        <p className="muted">
          Selected code-point range: [{range.start}, {range.end}). Save edits
          before anchoring a new task.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void command("add_task", {
              side,
              category,
              title,
              ...range,
              expected_sha256: head.sha256,
            });
          }}
        >
          <label>
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {[
                "meaning",
                "terminology",
                "quran",
                "hadith",
                "apparatus",
                "readability",
              ].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            Task description
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <button
            disabled={busy || dirty || stale || range.start === range.end}
          >
            Add anchored task
          </button>
        </form>
      </details>
      <TaskList
        side={side}
        tasks={document.tasks}
        version={head.number}
        sha={head.sha256}
        command={command}
        busy={busy}
      />
      <details>
        <summary>Accept this version for publication</summary>
        <p className="muted">
          Complete and stop a final verification session, then resolve all
          tasks. Acceptance is an expert attestation.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void command("accept", {
              side,
              expected_sha256: head.sha256,
              confirmed: accepted,
              reason: acceptReason,
            });
          }}
        >
          <label className="check">
            <input
              required
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
            />
            I reviewed this exact version against the shared publication
            standard.
          </label>
          <label>
            Acceptance note
            <input
              required
              value={acceptReason}
              onChange={(e) => setAcceptReason(e.target.value)}
            />
          </label>
          <button disabled={busy || dirty || stale}>
            Accept version {side.toUpperCase()}
          </button>
        </form>
      </details>
      <details>
        <summary>
          Version history · {document.versions.length} snapshots
        </summary>
        {document.versions.map((v) => (
          <details key={v.number}>
            <summary>
              v{v.number} · {v.actor} · {v.reason}
            </summary>
            <code>{v.sha256}</code>
            <pre dir="auto">{v.text}</pre>
          </details>
        ))}
      </details>
    </section>
  );
}
