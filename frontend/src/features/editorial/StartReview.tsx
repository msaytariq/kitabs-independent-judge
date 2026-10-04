"use client";
import { useState } from "react";
import type { Inputs } from "../../shared/types/editorial";
type Props = {
  busy: boolean;
  create: (id: string, rubric: string, inputs?: Inputs) => Promise<void>;
  open: (id: string) => unknown;
};
const defaultRubric =
  "Preserve meaning and significant details; use consistent terminology; verify Quran quotation boundaries and the declared translation edition; attribute hadith sources and scholarly judgments; resolve critical findings; ensure readable publication-ready prose.";
export function StartReview({ busy, create, open }: Props) {
  const [mode, setMode] = useState("paste"),
    [scope, setScope] = useState(""),
    [existing, setExisting] = useState(""),
    [rubric, setRubric] = useState(defaultRubric);
  const [inputs, setInputs] = useState<Inputs>({
    source: "",
    a: "",
    b: "",
    source_language: "ar",
    target_language: "en",
  });
  return (
    <div className="start-grid">
      <section className="panel">
        <span className="eyebrow">01 · Define the comparison</span>
        <h2>One source. Two versions.</h2>
        <p className="muted">
          Paste corresponding passages, or use a confirmed scope from the intake
          API. Both versions share the same publication standard.
        </p>
        <div className="tabs">
          <button
            className={mode === "paste" ? "selected" : ""}
            onClick={() => setMode("paste")}
          >
            Paste passages
          </button>
          <button
            className={mode === "scope" ? "selected" : ""}
            onClick={() => setMode("scope")}
          >
            Existing scope
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void create(scope, rubric, mode === "paste" ? inputs : undefined);
          }}
        >
          {mode === "paste" ? (
            <>
              <div className="row">
                <label>
                  Source language
                  <input
                    required
                    value={inputs.source_language}
                    onChange={(e) =>
                      setInputs({ ...inputs, source_language: e.target.value })
                    }
                  />
                </label>
                <label>
                  Translation language
                  <input
                    required
                    value={inputs.target_language}
                    onChange={(e) =>
                      setInputs({ ...inputs, target_language: e.target.value })
                    }
                  />
                </label>
              </div>
              {(["source", "a", "b"] as const).map((role) => (
                <label key={role}>
                  {role === "source"
                    ? "Original passage"
                    : `Version ${role.toUpperCase()}`}
                  <textarea
                    required
                    dir="auto"
                    rows={4}
                    value={inputs[role]}
                    onChange={(e) =>
                      setInputs({ ...inputs, [role]: e.target.value })
                    }
                  />
                </label>
              ))}
              <label className="check">
                <input required type="checkbox" />I checked that all three
                passages cover the same source content.
              </label>
            </>
          ) : (
            <label>
              Confirmed scope ID
              <input
                required
                value={scope}
                onChange={(e) => setScope(e.target.value)}
              />
            </label>
          )}
          <label>
            Publication standard
            <textarea
              required
              rows={4}
              value={rubric}
              onChange={(e) => setRubric(e.target.value)}
            />
          </label>
          <button className="primary" disabled={busy}>
            Create editorial review
          </button>
        </form>
      </section>
      <aside className="panel compact">
        <span className="eyebrow">Continue work</span>
        <h2>Open a saved review</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            open(existing);
          }}
        >
          <label>
            Review ID
            <input
              required
              value={existing}
              onChange={(e) => setExisting(e.target.value)}
            />
          </label>
          <button disabled={busy}>Open review</button>
        </form>
        <hr />
        <h3>What this measures</h3>
        <p>
          Editing and verification intervals, prior human work, decisions and
          versions. Unknown history remains unknown.
        </p>
        <p className="muted">
          No AI calls are made on this screen. Timer sessions are controlled by
          the editor; they do not detect attention. This is a local stand.
        </p>
      </aside>
    </div>
  );
}
