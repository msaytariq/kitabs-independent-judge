export type Side = "a" | "b";
export type Version = {
  number: number;
  text: string;
  sha256: string;
  at_ms: number;
  actor: string;
  reason: string;
};
export type Decision = {
  status: "confirmed" | "resolved" | "dismissed";
  version: number;
  reason: string;
  actor: string;
};
export type Task = {
  id: string;
  category: string;
  title: string;
  anchor: { version: number; quote: string; start: number; end: number };
  decision: Decision | null;
};
export type Session = {
  id: string;
  side: Side;
  stage: string;
  actor: string;
  status: "running" | "paused" | "stopped";
  version: number;
  intervals: { start_ms: number; end_ms: number | null }[];
};
export type EditorialSide = {
  versions: Version[];
  tasks: Task[];
  prior_work: {
    status: "unknown" | "none" | "reported";
    seconds: number | null;
    reason: string;
  };
  acceptance: null | {
    actor: string;
    version: number;
    at_ms: number;
    reason: string;
  };
};
export type SideMetrics = {
  editing_seconds: number;
  verification_seconds: number;
  tracked_seconds: number;
  prior_seconds: number | null;
  prior_status: string;
  total_seconds: number | null;
  pending_tasks: number;
  dismissed_tasks: number;
  stale_decisions: number;
  accepted: boolean;
};
export type Review = {
  id: string;
  revision: number;
  created_at_ms: number;
  updated_at_ms: number;
  scope_id: string;
  scope: {
    texts: Record<string, string>;
    hashes: Record<string, string>;
    source_language: string;
    target_language: string;
  };
  rubric: { text: string; sha256: string };
  sides: Record<Side, EditorialSide>;
  sessions: Session[];
  metrics: {
    sides: Record<Side, SideMetrics>;
    savings_percent: number | null;
    unavailable_reasons: string[];
  };
};
export type Command = (
  kind: string,
  params: Record<string, unknown>,
) => Promise<Review | null>;
export type Inputs = {
  source: string;
  a: string;
  b: string;
  source_language: string;
  target_language: string;
};
