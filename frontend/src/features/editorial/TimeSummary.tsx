import type { Review } from "../../shared/types/editorial";
import { formatSeconds } from "./helpers.mjs";
export function TimeSummary({ review }: { review: Review }) {
  const { metrics } = review;
  return (
    <section className="panel summary">
      <div>
        <span className="eyebrow">Editorial effort</span>
        <h2>Time to the same standard</h2>
        <p className="muted">
          Recorded intervals and declared prior work are shown separately.
        </p>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Human work</th>
              <th>Version A</th>
              <th>Version B</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>Prior work · declared</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>{formatSeconds(metrics.sides[s].prior_seconds)}</td>
              ))}
            </tr>
            <tr>
              <th>Editing · timed</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>
                  {formatSeconds(metrics.sides[s].editing_seconds)}
                </td>
              ))}
            </tr>
            <tr>
              <th>Final verification · timed</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>
                  {formatSeconds(metrics.sides[s].verification_seconds)}
                </td>
              ))}
            </tr>
            <tr className="total">
              <th>Total recorded / declared</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>{formatSeconds(metrics.sides[s].total_seconds)}</td>
              ))}
            </tr>
            <tr>
              <th>Remaining tasks</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>{metrics.sides[s].pending_tasks}</td>
              ))}
            </tr>
            <tr>
              <th>Publication acceptance</th>
              {(["a", "b"] as const).map((s) => (
                <td key={s}>
                  {metrics.sides[s].accepted ? "Accepted by editor" : "Pending"}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <div className="result-callout">
        <strong>
          {metrics.savings_percent === null
            ? "Time savings: not yet established"
            : `Version B time savings: ${metrics.savings_percent.toFixed(1)}%`}
        </strong>
        <p>
          {metrics.savings_percent === null
            ? "Both versions need acceptance, stopped timers and a complete history of prior work."
            : "Relative to version A, under this review’s rubric. This is one observation; it does not establish general platform superiority."}
        </p>
      </div>
    </section>
  );
}
