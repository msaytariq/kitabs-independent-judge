import type { Inputs, Review } from "../types/editorial";
import {apiUrl} from './base';
async function json<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      data.error?.message ||
        (Array.isArray(data.detail)
          ? data.detail.map((d: { msg: string }) => d.msg).join("; ")
          : data.detail) ||
        "Request failed.",
    );
  return data;
}
export const getReview = (id: string) =>
  json<Review>(`/api/editorial/${encodeURIComponent(id)}`);
export const createReview = (scope_id: string, rubric: string, actor: string) =>
  json<Review>("/api/editorial", { scope_id, rubric, actor });
export const commandReview = (
  review: Review,
  actor: string,
  kind: string,
  params: Record<string, unknown>,
) =>
  json<Review>(`/api/editorial/${review.id}/commands`, {
    expected_revision: review.revision,
    command_id: crypto.randomUUID(),
    actor,
    kind,
    params,
  });
export async function scopeFromTexts(inputs: Inputs) {
  const draft = await json<{
    id: string;
    materials: Record<string, { text: string; sha256: string }>;
  }>("/api/comparisons/text", inputs);
  const ranges = Object.fromEntries(
    Object.entries(draft.materials).map(([role, m]) => [
      role,
      { start: 0, end: Array.from(m.text).length, text_sha256: m.sha256 },
    ]),
  );
  return json<{ id: string }>(`/api/comparisons/${draft.id}/scopes`, {
    ranges,
    profile: inputs.source_language === "ar" ? "islamic-scholarly" : "general",
    confirmed: true,
  });
}
export const exportUrl = (id: string) =>
  apiUrl(`/api/editorial/${encodeURIComponent(id)}/export`);
