"use client";
import { useEditorialReview } from "./useEditorialReview";
import { StartReview } from "./StartReview";
import { SessionControls } from "./SessionControls";
import { TimeSummary } from "./TimeSummary";
import { VersionEditor } from "./VersionEditor";
import { exportUrl } from "../../shared/api/editorial";
export function EditorialWorkbench() {
  const work = useEditorialReview(),
    r = work.review;
  return (
    <main>
      <header>
        <div className="brand">
          <span className="brand-mark">IJ</span>
          <span>
            Independent Judge<small>EDITORIAL WORKBENCH</small>
          </span>
        </div>
        <span className="environment">Local stand · human review</span>
      </header>
      <section className="intro">
        <span className="eyebrow">From assessment to publication</span>
        <h1>
          Make editorial work
          <br />
          measurable.
        </h1>
        <p>
          Compare the work needed to bring two versions to one publication
          standard. Preserve the evidence behind every decision.
        </p>
      </section>
      <section className="operator">
        <label>
          Editor label
          <input
            placeholder="Your name or study participant ID"
            value={work.actor}
            onChange={(e) => work.setActor(e.target.value)}
            maxLength={80}
          />
        </label>
        <p>
          Self-declared identity for this local study. Use the same label for
          all your sessions.
        </p>
        {r && (
          <div className="actions">
            <button disabled={work.busy} onClick={() => void work.open(r.id)}>
              Refresh saved state
            </button>
            <a className="button" href={exportUrl(r.id)}>
              Export evidence JSON
            </a>
          </div>
        )}
      </section>
      {work.error && (
        <div className="error" role="alert">
          {work.error}
        </div>
      )}
      {work.busy && (
        <p role="status" className="muted">
          Saving / loading…
        </p>
      )}
      {!r ? (
        <StartReview busy={work.busy} create={work.create} open={work.open} />
      ) : (
        <>
          <div className="review-meta">
            <span>
              Review <code>{r.id}</code>
            </span>
            <span>
              Revision {r.revision} · <a href="/">New comparison</a>
            </span>
          </div>
          <TimeSummary review={r} />
          <SessionControls
            review={r}
            command={work.command}
            busy={work.busy}
            actor={work.actor}
          />
          <section className="panel source">
            <div>
              <span className="eyebrow">Shared evidence</span>
              <h2>Original passage</h2>
              <pre dir="auto">{r.scope.texts.source}</pre>
            </div>
            <details>
              <summary>Agreed publication standard</summary>
              <p>{r.rubric.text}</p>
              <code>{r.rubric.sha256}</code>
            </details>
          </section>
          <div className="versions">
            {(["a", "b"] as const).map((side) => (
              <VersionEditor
                key={`${r.id}-${side}`}
                side={side}
                document={r.sides[side]}
                command={work.command}
                busy={work.busy}
              />
            ))}
          </div>
          <section className="panel">
            <h2>Session record</h2>
            {r.sessions.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Editor</th>
                      <th>Version</th>
                      <th>Activity</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.sessions.map((s) => (
                      <tr key={s.id}>
                        <td>{s.actor}</td>
                        <td>
                          {s.side.toUpperCase()} · v{s.version}
                        </td>
                        <td>{s.stage}</td>
                        <td>{s.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted">No work sessions recorded yet.</p>
            )}
          </section>
        </>
      )}
      <footer>
        Human decisions remain explicit. No automatic claim of time savings,
        religious authenticity or platform superiority.
      </footer>
    </main>
  );
}
