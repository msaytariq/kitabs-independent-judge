"use client";
import { useState } from "react";
import type {
  Command,
  EditorialSide,
  Side,
} from "../../shared/types/editorial";
export function PriorWork({
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
  const [status, setStatus] = useState(document.prior_work.status),
    [minutes, setMinutes] = useState(""),
    [reason, setReason] = useState("");
  return (
    <details>
      <summary>Prior human work: {document.prior_work.status}</summary>
      <p className="muted">
        Include editing already done inside the vendor’s workflow. Historical
        time without a record is unknown.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void command("prior_work", {
            side,
            status,
            seconds:
              status === "unknown"
                ? null
                : status === "none"
                  ? 0
                  : Number(minutes) * 60,
            reason,
          });
        }}
      >
        <label>
          History
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <option value="unknown">Unknown / not recorded</option>
            <option value="none">
              No prior human work · explicit declaration
            </option>
            <option value="reported">Time available · self-report</option>
          </select>
        </label>
        {status === "reported" && (
          <label>
            Recorded minutes
            <input
              required
              type="number"
              min="0"
              step="any"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
            />
          </label>
        )}
        <label>
          Evidence or explanation
          <input
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        <button disabled={busy}>Record prior-work declaration</button>
      </form>
    </details>
  );
}
